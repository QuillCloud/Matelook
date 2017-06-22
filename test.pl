#!/usr/bin/perl -w
open $F,"<", "cloud.txt" or die $!;
@new = ();
while ($line = <$F>) {
    if ($line =~ /age/) {
	push @new, "age = 3\n";
    }
    else{
	push @new, $line;
    }
}
close $F;
open $F,">", "cloud.txt" or die $!;
print $F join("", @new);
close $F;
