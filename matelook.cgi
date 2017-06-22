#!/usr/bin/perl -w

# written by Yunhe Zhang z5045582 Octorber 2016
# for COMP9041 Assignment2
# http://cgi.cse.unsw.edu.au/~z5045582/ass2/matelook.cgi

use List::Util qw(first);
use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;
use POSIX qw(strftime);


sub main() {
    
    # do some operation first, like set cookie, determine the current user...
    &pre_operation();
    
    # print start of HTML ASAP to assist debugging if there is an error in the script
    print &page_header();
    
    # Now tell CGI::Carp to embed any warning in HTML
    warningsToBrowser(1);

    # print login part
    print login_print();

    # determine the page body
    if (defined param("post")) {
	#print the page which used to make new post
	print &com_rep_page(param("post"), "posts");

    } elsif (defined param("comment")) {
	# print the page which used to make new comment for posts
	print &com_rep_page(param("comment"), "comments");

    } elsif (defined param("reply")) {
	#print the page which used to make new rely for comments
	print &com_rep_page(param("reply"), "replies");

    } elsif (defined param("search")) {
	#print the search name page
        print &search_page(param("search"));

    } elsif (defined param("search_post")) {
	#print the search posts page
	print &search_posts_page(param("search_post"));

    } elsif (defined param("edit") || defined param("remove_mate") || defined param("add_mate")) {
	#print the edit mates page(add or remove mates)
	$state = "";
	if (defined param("remove_mate")) {
	    &remove_mate_sub(param("remove_mate"));
	} elsif (defined param("add_mate")) {
	    &add_mate_sub(param("add_mate"));
	}
	print &edit_mates();

    } else {
	# print user's page
	print &user_page();
    }

    # print the page trail
    print &page_trailer();
}

#
#some operations before printing the page
#
sub pre_operation {

    # initialize some global value
    $debug = 1;
    $users_dir = "dataset-medium";
    @users = sort(glob("$users_dir/*"));
    $user_to_show = "";

    # get the cookie, $x store current user page, $z store current login user
    if ($ENV{HTTP_COOKIE} =~ /\bx=(.*);/) {
        $x = $1;
    } else {
        $x = "";
    }
    $last_user = $x;
    if ($ENV{HTTP_COOKIE} =~ /\bz=(.*)/) {
        $z = $1;
    } else {
        $z = "";
    }

    # for make new comment or reply operation, update the comments or replies
    if (param("submit")) {
        if (param("add_content") eq "") {
	    @repeat_sub = split(/ /, param("dir"));
	    print &com_rep_page($repeat_sub[0], $repeat_sub[1]);
        } else {
            &create_com_rep();
        }
    }

    #create a hash, zid => full_name
    %name_zid = ();
    for my $user (@users) {
        if ($user =~ /dataset-medium\/(.*)/) {
            $user_zid = $1;
        }
        open $up, "$user/user.txt" or die "can not open $details_filename: $!";
        while($upline = <$up>) {
            if ($upline =~ /full_name=(.*)/) {
                $name_zid{$user_zid} = $1;
            }
        }
    }

    #read login value and check login or logout
    $login_flag = "";
    if (defined param("login")) {
	$login_flag = &check_login();
    }
    if (defined param("logout")) {
	$z = "";
    }

    # if any user's name is clicked, show this user's page
    foreach $c_mate (@users) {
	$c_mate =~ m/(z[0-9]{7})/g;
	if (defined param($1)) {
	    $user_to_show = $1;
	    $user_to_show = "$users_dir/$user_to_show";
	    last;
	}
    }

    # if any user succeed login, show this user's page
    if ($login_flag =~ /z\d+/) {
	$user_to_show = "$users_dir/$login_flag";
	$z = $login_flag;
    }
    
    
    # if the next user button is clicked, show the next user
    if (defined (param("n"))) {
	$n = param("n") + 1;
	$user_to_show  = $users[$n % @users];
    }
    
    # if the user to show still not be determined, use cookie $x as the user
    # if cookie $x not be set, show the first user's page
    if ($user_to_show eq "") {
	if ($x =~ /z\d+/) {
	    $user_to_show = "$users_dir/$x";
	} 
	else {
	    $user_to_show = $users[0];
	}
    }

    # update the current user's location
    $n = first {$users[$_] eq $user_to_show } 0..$#users;
    
    # get user's information
    my $details_filename = "$user_to_show/user.txt";
    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    %private_detail = ();
    %public_detail = ();
    while ($contents = <$p>) {
        $contents =~ /(.*)\=(.*)/;
        my $temp1 = $1;
        my $temp2 = $2;
	if ($temp1 =~ /full_name|zid|mates/) {
            $public_detail{$temp1} = $temp2;
        } else {
            $private_detail{$temp1} = $temp2;
        }
    }
    $x = $public_detail{"zid"};
    close $p;
    if ($z ne "") {
	open my $z_user, "$users_dir/$z/user.txt" or die $!;
	while (my $z_line = <$z_user>) {
	    if ($z_line =~ /^mates=/) {
		$z_detail_mate = $z_line;
		last;
	    }
	}
    }
    close $z_user;
    # not all pages need the operations below like search page
    if (defined param("search") || defined param("search_posts")) {
	return;
    }
    if (defined param("edit") || defined param("add_mate") || defined param("remove_mate")) {
	return;
    }

    # check if the user has image
    $profile = "$user_to_show/profile.jpg";
    if (-f $profile) {
        $profile = "<img src=\"http://cgi.cse.unsw.edu.au/~z5045582/ass2/$profile\" height=\"150\" width=\"150\">";
    } else {
        $profile = "";
    }
    
    # get the user's posts, if login user in his/her own page, get recent post and thier mates' post
    my @getpost = sort(glob("$user_to_show/posts/*"));
    $post = "";
    foreach $temp_p (reverse @getpost) {
        $post .= &posts("$temp_p");
	if ($x eq $z && $z ne "") {
	    $post .= &mates_post();
	    last;
	}
    }
    
    # get the mates of the user;
    $mate_link = &mates($public_detail{"mates"});
}

#
# sub for print edit mates page
#
sub edit_mates {
    my @mate_e = ($z_detail_mate =~ m/z[0-9]{7}/g);
    $edit_list = "";
    for my $mate (@mate_e) {
	$edit_list .= &remove_mates($mate);
    }
    return <<eof
<div class="matelook_edit">
$edit_list
</div>
<form method="POST" action="" class="com_rep_form">
Input zid to add a new mate <input type="txt" name="add_mate" class="input_search"></form>
<div class="com_rep_form"><form name="F1" method="POST" action="">
$state

<input type="submit" value="Back" class="click_log">
</form>
</div>
eof
}

#
# create the current mates and remove button for the edit mates page
#
sub remove_mates {
    my ($getrm) = @_;
    return <<eof
<form method="POST" action=""> $name_zid{$getrm}<input type="hidden" name="remove_mate" value="$getrm"><input type="submit" name="remove" value="remove" class="click_name_b"></form>
eof
}

#
# sub for removing mates
#
sub remove_mate_sub {
    my ($remove_zid) = @_;
    $z_detail_mate =~ s/$remove_zid//g;
    my @mate_e = ($z_detail_mate =~ m/z[0-9]{7}/g);
    my $new_mates = join(", ", @mate_e);
    $new_mates = "mates=\[$new_mates\]\n";
    my @new = ();
    open my $F, "<", "$users_dir/$z/user.txt" or die "can not open $user_to_show/user.txt: $!";
    while (my $F_line = <$F>) {
	if ($F_line =~ /^mates=/) {
	    push @new, $new_mates;
	}
	else{
	    push @new, $F_line;
	}
    }
    close $F;
    open my $FF,">", "$users_dir/$z/user.txt" or die $!;
    print $FF join("", @new);
    close $FF;
    $state = "Remove Successful!";
}

#
# sub for adding mate, need to check whether the input zid is valid or not.
#
sub add_mate_sub {
    my ($add_zid) = @_;
    if (-e "$users_dir/$add_zid") {
	if ($z_detail_mate =~ /$add_zid/) {
	    $state = "Add Failed, $name_zid{$add_zid} is alreay your mate!";
	} elsif ($add_zid eq $z)  {
	    $state = "Add Failed, Can't add yourself as mate.";
	} else {
	    my @mate_e = ($z_detail_mate =~ m/z[0-9]{7}/g);
	    push @mate_e, $add_zid;
	    my $new_mates = join(", ", @mate_e);
	    $new_mates = "mates=\[$new_mates\]\n";
	    $z_detail_mate = $new_mates;
	    my @new = ();
	    open my $F, "<", "$users_dir/$z/user.txt" or die "can not open $user_to_show/user.txt: $!";
	    while (my $F_line = <$F>) {
		if ($F_line =~ /^mates=/) {
		    push @new, $new_mates;
		}
		else{
		    push @new, $F_line;
		}
	    }
	    close $F;
	    open my $FF,">", "$users_dir/$z/user.txt" or die $!;
	    print $FF join("", @new);
	    close $FF;
	    $state = "Add Successful!"
	}
    } else {
	$state = "Add Failed, Zid not exits!";
    }
}

#
# sub for show the user's page
#
sub user_page {
    $add_post = "Posts";
    if ($z eq $x && $z ne "") {
        $add_post = <<eof
<form>Posts<input type="hidden" name="post" value="$user_to_show"> <input type="submit" name="" value="Add Post" class="make_post"></form>
eof
    }
    return <<eof
</form>
<form class="matelook_search">
<input type="text" name="search" placeholder="Search Name.." class="input_search">
</form>
<form class="matelook_search">
<input type="text" name="search_post" placeholder="Search Posts.." class="input_search">
</form>
<p>
<div class="matelook_detail">
$profile<br>$public_detail{"full_name"}<br>$public_detail{"zid"}
</div>
$mate_link
<p>
$add_post
$post
<p>
<form name="F1" method="POST" action="">
    <input type="hidden" name="n" value="$n">
    <input type="submit" value="Next user" class="click_log">
</form>
eof
}

#
# sub for print the search name page
#
sub search_page {
    my ($search_name) = @_;
    $search_name = lc $search_name;
    @search_result = ();
    foreach my $user (keys %name_zid) {
	if ((lc $name_zid{$user}) =~ /$search_name/) {
	    push(@search_result, $user);
	}
    }
    if ($#search_result eq -1) {
	$search_output = "Sorry, No Matching Results!"
    } elsif ($search_name eq "") {
	$search_output = "Please Input Something!"
    } else { 
	$search_output = "<form name=\"F2\" method=\"POST\" action=\"\">";
	foreach my $user (@search_result) {
	    if (-f "$users_dir/$user/profile.jpg") {
		$search_output .= "<input type=\"submit\" name=\"$user\" value=\"\" style=\"width:50px;height:50px;background-image: url(\'http://cgi.cse.unsw.edu.au/~z5045582/ass2/$users_dir/$user/profile.jpg\')\" class=\"image_button\">";
		$search_output .= "<input type=\"submit\" name=\"$user\" value=\"$name_zid{$user}\" class=\"click_name_b\"><br><br>";
	    }
	    else {
		$search_output .= "        ";
		$search_output .= "<input type=\"submit\" name=\"$user\" value=\"$name_zid{$user}\" class=\"click_name_b\"> ";
		$search_output .= "<br><br>";
	    }
	}
	$search_output .= "</form>";
    }
    return <<eof
<form class = "matelook_search">
<input type="text" name="search" placeholder="Search Name.." class="input_search">
</form>
<p>
<div class="search_page">
$search_output
</div>
<form name="F1" method="POST" action="">
    <input type="submit" value="Back" class="click_log">
</form>
eof
}

#
# sub for print search posts page
#
sub search_posts_page {
    my ($search_post) = @_;
    $result_post = "";
    if ($search_post ne "") {
	$search_post = lc $search_post;
	for my $user (@users) {
	    my @get_p = (glob("$user/posts/*"));
	    for my $post_dir (@get_p) {
		open my $postfile, "$post_dir/post.txt" or die "can not open $user_filename: $!";
		while ($pf_line = <$postfile>) {
		    if ((lc $pf_line) =~ /^message=(.*)/) {
			$search_post_message = $1;
			$search_post_message =~ s/$search_post/<mark>$search_post<\/mark>/g;
		    } elsif ($pf_line =~ /^time=(.*)T(.*)\+/) {
			$search_post_time = "$1 $2";
		    } elsif ($pf_line =~ /^from=(.*)/) {
			$search_post_from = &trans_zid($1,"click_name_p");
		    }
		}
		if ($search_post_message =~ /$search_post/) {
		    $result_post .= "<form class=\"matelook_posts\"><br>$search_post_time $search_post_from<br><br>$search_post_message<br><br><\/form><br>";
		}
	    }
	}
    } else {
	$result_post = "Please Input Something!";
    }
    if ($result_post eq "") {
	$result_post = "Sorry, No Matching Results!";
    }
    return <<eof
<form class="matelook_search">
<input type="text" name="search_post" placeholder="Search Posts.." class="input_search">
</form><br>
$result_post<br>
<form name="F1" method="POST" action="">
    <input type="submit" value="Back" class="click_log">
</form>
eof
} 

#
# HTML placed at the top of every page
#
sub page_header {
    return <<eof
Content-Type: text/html;charset=utf-8
Set-Cookie: x=$x;
Set-Cookie: z=$z;

<!DOCTYPE html>
<html lang="en">
<head>
<title>matelook</title>
<link href="matelook.css" rel="stylesheet">
</head>
<body class="matelook_body">
<div class="matelook_heading">
MATELOOK
</div>
eof
}


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

#
# get the posts to show in user's page
#
sub posts {
    my ($get) = @_;
    open my $post_line, "$get/post.txt" or die "can not open $details_filename: $!";
    while ($temp_posts = <$post_line>) {
	if ($temp_posts =~ /^message=(.*)/) {
	    $post_message = $1;
	     my @zid_array = ($post_message =~ m/z[0-9]{7}/g);
            for my $zid (@zid_array) {
                $zid_rep = &trans_zid($zid, "click_name_p");
                $post_message =~ s/$zid/$zid_rep/g;
            }
	} elsif ($temp_posts =~ /^time=(.*)T(.*)\+/) {
	    $post_time = "$1 $2";
	} elsif ($temp_posts =~ /^from=(.*)/) {
	    $post_name = $name_zid{$1};
	}
    }
    close $post_line;
    $comment = "";
    if (-e "$get/comments") {
	my @getcomment = (glob("$get/comments/*"));
	for $gc (reverse @getcomment) {
	    $comment .= &comments($gc);
	}
    }
    $rep_post = "";
    if ($z ne "") {
	$rep_post = <<eof
<form><input type="hidden" name="comment" value="$get"> <input type="submit" name="" value="Add Comment" class="make_comment"></form>
eof
    }
    return <<eof
<p>
<div class = "matelook_posts">
<form> $post_time

 $post_message</from>

$comment
$rep_post
</div>
eof
}

#
# get the mates' posts, if logined user in his/her own page, call this sub
#
sub mates_post {
    my @matelist = ($public_detail{"mates"} =~ m/z[0-9]{7}/g);
    $mates_post = "";
    for my $mates (@matelist) {
	$mates_post .= "<br>$name_zid{$mates}'s Posts<br>";
	@get_mate_post = sort(glob("$users_dir/$mates/posts/*"));
	for $gmp (reverse @get_mate_post) {
	    $mates_post .= &posts($gmp);
	}
    }
    return $mates_post;
}

#
# get the comments for posts, call in posts sub
#
sub comments {
    my ($comdir) = @_;
    open my $comment_line, "$comdir/comment.txt" or die "can not open $details_filename:$!";
    while ($com_content = <$comment_line>) {
	if ($com_content =~ /^message=(.*)/) {
	    $com_message = $1;
	    my @zid_array = ($com_message =~ m/z[0-9]{7}/g);
            for my $zid (@zid_array) {
                my $zid_rep = &trans_zid($zid, "click_name_c");
                $com_message =~ s/$zid/$zid_rep/g;
            }
	} elsif ($com_content =~ /^from=(.*)/) {
	    $com_user = &trans_zid($1, "click_name_c");
	} elsif ($com_content =~ /^time=(.*)T(.*)\+/) {
	    $com_time = "$1 $2";
	}
    }
    close $comment_line;
    $reply = "";
    if (-e "$comdir/replies") {
	my @getreply = (glob("$comdir/replies/*"));
	for $replyc (reverse @getreply) {
            $reply .= &replies($replyc);
        }
    }
    $rep_comment = "";
    if ($z ne "") {
       $rep_comment = <<eof
<form><input type="hidden" name="reply" value="$comdir"> <input type="submit" name="" value="Add reply" class="make_reply"></form>
eof
    }
    return <<eof
<div class="matelook_comment">
<form>   $com_time  From:$com_user

 $com_message</form>
 $reply
 $rep_comment
</div>
eof
}

#
#get replies for comments, call in comments sub
#
sub replies {
    my ($repdir) = @_;
    open my $reply_line, "$repdir/reply.txt" or die "can not open $details_filename:$!";
    while ($rep_content = <$reply_line>) {
        if ($rep_content =~ /^message=(.*)/) {
            $rep_message = $1;
	    my @zid_array = ($rep_message =~ m/z[0-9]{7}/g);
	    for my $zid (@zid_array) {
		my $zid_rep = &trans_zid($zid, "click_name_r");
		$rep_message =~ s/$zid/$zid_rep/g;
	    }
        } elsif ($rep_content =~ /^from=(.*)/) {
            $rep_user = &trans_zid($1, "click_name_r");
        } elsif ($rep_content =~ /^time=(.*)T(.*)\+/) {
            $rep_time = "$1 $2";
        }
    }
    close $reply_line;
    return <<eof
<div class="matelook_reply">
<form>  $rep_time  From:$rep_user

  $rep_message</form>
</div>
eof
}

#
# get mates for user's page
#
sub mates {
    my ($getm) = @_;
    my @matelist = ($getm =~ m/z[0-9]{7}/g); 
    $res = "";
    foreach $m (@matelist) {
	open my $pm, "$users_dir/$m/user.txt" or die "can not open $details_filename: $!";
	while(my $m_content = <$pm>) {
	    if ($m_content =~ /full_name=(.*)/) {
		$m_name = $1;
	    }
	}
	close $pm;
	$m_space = "";
	$m_len = (length($m_name) - 6) / 2;
	while ($m_len > 0) {
	    $m_space .= " ";
	    $m_len--;
	}
	if (-f "$users_dir/$m/profile.jpg") {
	    $res .= "<input type=\"submit\" name=\"$m\" value=\"$m_name\" class=\"click_name_b\">";
	    $res .= "<input type=\"submit\" name=\"$m\" value=\"\" style=\"width:40px;height:40px;background-image: url(\'http:/\/cgi.cse.unsw.edu.au/~z5045582/ass2/$users_dir/$m/profile.jpg\')\" class=\"image_button\">    ";
	}
	else {
	    $res .= "<input type=\"submit\" name=\"$m\" value=\"$m_name\" class=\"click_name_b\">";
	    $res .= "        ";
	}
    }
    $edit = "";
    if ($x eq $z) {
	$edit = "<input type=\"submit\" name=\"edit\" value=\"Edit Mates\" class=\"click_log\">";
    }
    return <<eof
<p>
<form name="edit" method="POST" action="">Mates $edit</form><br>
<div class="matelook_mates">
<form name="F2" method="POST" action="">$res
</form>
</div>

eof
}

#
#check whether have a login value, if so, check username and password return proper value to login_flag;
#
sub check_login {
    my $username = "";
    my $password = "";
    if (defined param("login")) {
	$username = param("username");
	$password = param("password");
	if ($username ne "") {
	    if ($password ne "") {
		if (exists $name_zid{$username}) {
		    open my $cl_p, "$users_dir/$username/user.txt" or die "can not open $details_filename: $!";
		    while (my $cl_line = <$cl_p>) {
			if ($cl_line =~ /password=(.*)/) {
			    if ($password eq $1) {
				return $username;
			    }
			    else {
				return "Incorrect Password!";
			    }
			}
		    }
		}
		else {
		    return "Username not exists!";
		}
	    } 
	    else {
		return "Please Enter Password!";
	    }
	} 
	else {
	    return "Please Enter Username!";
	}
    } 
    else {
	return "";
    }
}

#
# print the login parts
#
sub login_print {
    if ($z ne "") {
	$login_name = &trans_zid($z, "click_name_b");
	return <<eof
<form name="LOGOUT" method="POST" action="" class="matelook_login">
WELCOME TO MATELOOK!<br>
$login_name<br>
<input type="submit" name="logout" value="logout" class="click_log">
</form>
eof
    } else {
	return <<eof
<form name="LOGIN" method="POST" action="" class="matelook_login">
UserName:<input type="text" name="username" class="input_search">
PassWord:<input type="password" name="password" class="input_search">
<input type="submit" name="login" value="login" class="click_log">
<br>
$login_flag
</form>
eof
    }
}

#
# make post, comment or reply page
#
sub com_rep_page {
    my ($getdir, $flag) = @_;
    return <<eof
<form name="add_com_rep" method="POST" action="" class="com_rep_form">
<textarea cols="50" rows="10" name="add_content" value="" class="textarea"></textarea>
<input type="hidden" name="dir" value="$getdir $flag">
<input type="submit" name="submit" value="submit" class="click_log">        <input type="submit" name="back" value="back" class="click_log">
<form>
eof
}

#
# sub for creating post, comment and reply
#
sub create_com_rep {
    @getdir = split(/ /, param("dir")); 
    mkdir("$getdir[0]/$getdir[1]")  unless(-d "$getdir[0]/$getdir[1]");
    my @getfile = sort(glob("$getdir[0]/$getdir[1]/*"));
    my $new = $#getfile + 1;
    mkdir("$getdir[0]/$getdir[1]/$new") unless(-d "$getdir[0]/$getdir[1]/$new");
    my $file = "";
    if ($getdir[1] =~ /comments/) {
	$file = "comment.txt";
    } elsif ($getdir[1] =~ /replies/) {
	$file = "reply.txt";
    } elsif ($getdir[1] =~ /posts/) {
	$file = "post.txt";
    }
    my $messageStr = param("add_content");
    my $timeStr = strftime "%Y-%m-%dT%H:%M:%S\+0000", localtime;
    open my $F, '>', "$getdir[0]/$getdir[1]/$new/$file" or die $!;
    print $F "from=$z\n";
    print $F "time=$timeStr\n";
    print $F "message=$messageStr\n";
    close $F;
}

#
# translate zid to a linked name
#
sub trans_zid {
    my ($get_zid, $get_class) = @_;
    return "<input type=\"submit\" name=\"$get_zid\" value=\"$name_zid{$get_zid}\" class=\"$get_class\">";
}
main();
