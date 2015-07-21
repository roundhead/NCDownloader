#!/bin/sh
echo $1
python3 refine-buka/buka.py "$1" #./aaa
convert  -page a4 -adjoin $2/*.png target.pdf
rm -fr $2
rm $1
mv target.pdf "$3"
