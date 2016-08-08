#!/usr/bin/perl
use DBI;
use Mojolicious::Lite;
use Mojo::JSON qw(decode_json encode_json);
use strict;
use warnings;

open(IN, "<", "./config.json") or die("erorr: $!");
my $conf = decode_json(do {local $/; <IN>})->{DNS_API};
my @DBINFO = @{$conf->{DBINFO}};
my $flag_file = $conf->{FLAG_FILE};
close(IN);

sub set_flag {
    open(OUT, ">", $flag_file) or die("error: $!");
    print OUT "CHANGED";
    close(OUT);
}

get '/' => sub {
    my $self = shift;
    $self->render(text=>encode_json({status=>'LIVE'}));
};

get '/records/:id' => {id => undef} => sub {
    my $self = shift;
    my $id = $self->param('id');
    my @bind_values = ($id);
    my $query = 'SELECT * FROM dns' . ($id ? ' WHERE id=?' : '') . ';';
    my $dbh = DBI->connect(@DBINFO);
    my $ary_ref;
    if ($id) {
        $ary_ref = $dbh->selectrow_hashref($query, +{Slice=>{}}, @bind_values);
    } else {
        $ary_ref = $dbh->selectall_arrayref($query, +{Slice=>{}});
    }
    $dbh->disconnect;
    $self->render(text=>encode_json($ary_ref));
};

post '/records' => sub {
    my $self = shift;
    my @bind_values = (
        $self->param('domain'),
        $self->param('ipv4_address'),
        $self->param('record_type'),
        $self->param('host')
        );
    my $query = 'INSERT INTO dns ' .
        '(domain, ipv4_address, record_type, host) '.
        'VALUES (?, ?, ?, ?);';
    my $dbh = DBI->connect(@DBINFO);
    $dbh->do($query, {}, @bind_values) or die $dbh->errstr;
    my $lid = $dbh->last_insert_id(undef, undef, 'dns', 'id');
    $dbh->disconnect;
    &set_flag;
    $self->render(text=>encode_json({id => $lid}));
};

del '/records/:id' => sub {
    my $self = shift;
    my @bind_values = ($self->param('id'));
    my $query = 'DELETE FROM dns WHERE id=?;';
    my $dbh = DBI->connect(@DBINFO);
    $dbh->do($query, {}, @bind_values) or die $dbh->errstr;
    $dbh->disconnect;
    &set_flag;
    $self->render(text=>encode_json({status => 'Deleted'}));
};

put '/records/:id' => sub {
    my $self = shift;
    my @bind_values = (
        $self->param('host'),
        $self->param('ipv4_address'),
        $self->param('record_type'),
        $self->param('domain'),
        $self->param('id'));
    my $query = 'UPDATE dns SET ' .
        'host=?, ipv4_address=?, record_type=?, domain=? ' .
        'WHERE id=?';
    my $dbh = DBI->connect(@DBINFO);
    $dbh->do($query, {}, @bind_values);
    $dbh->disconnect;
    &set_flag;
    $self->render(text=>encode_json({status => 'Updated'}));
};

any '/*path' => {path => undef} => sub {
    my $self = shift;
    $self->render(text=>encode_json({message => 'Method not Allowed'}));
};

app->start;
