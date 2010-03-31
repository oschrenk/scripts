#! /bin/sh

# prefix to the svn repository
svnrepo=http://host/svn/

# take the name of the project from parameter
project=$1

# use local instead of global svn authorsfile
authorsfile=~/.git-svn-local.authorsfile

rm -rf tmp
mkdir tmp
cd tmp

echo $svnrepo/$project/trunk/

git svn init $svnrepo/$project/trunk/ --no-metadata
git config svn.authorsfile $authorsfile
git svn fetch


cd ..
git clone tmp $project
 