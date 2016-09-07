#!/usr/bin/perl
use DBI;
use Mojolicious::Lite;
use Mojo::JSON qw(decode_json encode_json);
use Net::OpenSSH;
use strict;
use warnings;

open(IN, '<', './config.json') or die("error: $!");
my $conf = decode_json(do {local $/; <IN>})->{RPROXY_API};
my @DBINFO =@{$conf->{DBINFO}};
my $flag_file = $conf->{FLAG_FILE};
close(IN);

sub set_flag {
    open(OUT, ">", $flag_file) or die("error: $!");
    print OUT "CHANGED";
    close(OUT);
}

sub get_records {
    my $id = shift;
    my @bind_values = ($id);
    my $query = 'SELECT * FROM rproxy' .
        ($id ? ' WHERE id=?' : '') .
        ';';
    my $dbh = DBI->connect(@DBINFO);
    my $ary_ref;
    if ($id) {
        $ary_ref = $dbh->selectrow_hashref($query, +{Slice=>{}}, @bind_values);
    } else {
        $ary_ref = $dbh->selectall_arrayref($query, +{Slice=>{}});
    }
    $dbh->disconnect;
    return $ary_ref;
}

sub set_record {
    my ($host, $upstream) = @_;
    my @bind_values = ($host, $upstream);
    my $query = 'INSERT INTO rproxy' .
        ' (host, upstream)' .
        ' VALUES (?, ?);';
    my $dbh = DBI->connect(@DBINFO);
    my $status = $dbh->do($query, {}, @bind_values);
    my $lid = $dbh->last_insert_id(undef, undef, 'rproxy', 'id');
    $dbh->disconnect;
    return $lid, $status;
}

sub update_record {
    my ($id, $host, $upstream) = @_;
    if (defined($host) && defined($upstream)) {
        return 1;
    }
    my @bind_values = ();
    my $query = 'UPDATE rproxy SET';
    if ($host) {
        $query .= ' host=?';
        push(@bind_values, $host);
    }
    if ($upstream) {
        $query .= ' upstream=?';
        push(@bind_values, $upstream);
    }
    $query .=  ' WHERE id=?;';
    push(@bind_values, $id);
    my $dbh = DBI->connect(@DBINFO);
    my $status = $dbh->do($query, {}, @bind_values);
    $dbh->disconnect;
    return $status
}

sub delete_record {
    my $id = shift;
    my @bind_values = ($id);
    my $query = 'DELETE FROM rproxy WHERE id=?;';
    my $dbh = DBI->connect(@DBINFO);
    my $status = $dbh->do($query, {}, @bind_values);
    $dbh->disconnect;
    return $status;
}

sub error {
    return {message=>shift};
}

sub save_conf {
    my ($host, $upstream) = @_;
    my $nginx_conf = qq(
server {
    listen 80;
    server_name $host.charakoba.com;

    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header Host \$http_
        host;
    proxy_redirect off;
    proxy_max_temp_file_size 0;

    location / {
        proxy_pass http://$upstream;
    }
});
    open(OUT, '>', "$conf->{CONF_PATH}/$host.proxy.conf");
    print OUT $nginx_conf;
    close(OUT);
}

get '/' => sub {
    my $self = shift;
    $self->render(text=>encode_json({status=>'LIVE'}));
};

get '/records' => sub {
    my $self = shift;
    my $records = &get_records;
    $self->render(json=>$records);
};

get '/records/:id' => sub {
    my $self = shift;
    my $id = $self->param('id');
    if ($id !~ /^\d+$/) {
        $self->render(text=>error("ID needs to be number"));
        return;
    }
    my $records = &get_records($id);
    $self->render(json=>$records);
};

post '/records' => sub {
    my $self = shift;
    my @record = ($self->param('host'), $self->param('upstream'));
    my ($lid, $status) = set_record(@record);
    my $record = get_records($lid);
    if ($status) {
        $self->render(json=>$record);
        &set_flag;
    } else {
        $self->render(
            json=>error('RECORD INSERT ERROR'),
            status=>400);
    }
};

put '/records/:id' => sub {
    my $self = shift;
    my $id = $self->param('id');
    my $host = $self->param('host');
    my $upstream = $self->param('upstream');
    my $status = update_record($id, $host, $upstream);
    if ($status) {
        $self->render(json=>get_records($id));
        &set_flag;
    } else {
        $self->render(
            json=>error('RECORD UPDATE ERROR'),
            status=>400);
    }
};

del '/records/:id' => sub {
    my $self = shift;
    my $id = $self->param('id');
    my $status = delete_record($id);
    if ($status) {
        $self->render(json=>{message=>'SUCCESS'});
        &set_flag;
    } else {
        $self->render(
            json=>error('RECORD DELETE ERROR'),
            status=>400);
    }
};


post '/sync' => sub {
    my $self = shift;
    for my $record (@{&get_records}){
        save_conf($record->{host}, $record->{upstream});
    }
    for my $rproxy_host (@{$conf->{RPROXY_HOSTS}}) {
        my $ssh = Net::OpenSSH->new($rproxy_host, $conf->{RPROXY_INFO});
        my %rsync_opts = (archive => 1,
                          compress => 1,
                          delete => 1,
                          rsh => "ssh -i $conf->{RSYNC_KEY} " .
                              "-o 'UserKnownHostsFile=/dev/null' -o 'StrictHostKeyChecking=no'");
        $ssh->rsync_put(\%rsync_opts, "$conf->{CONF_PATH}/", "root\@$rproxy_host:/etc/nginx/conf.d/");
        if ($ssh->error) {
            $self->render(json=>error("rsync failed: " . $ssh->error));
        }
    }
    $self->render(text=>"SUCCESS");
};

any '/*path' => {path => undef} => sub {
    my $self = shift;
    $self->render(
        json=>{message => 'Method Not Allowed'},
        status=>405);
};

app->start;
