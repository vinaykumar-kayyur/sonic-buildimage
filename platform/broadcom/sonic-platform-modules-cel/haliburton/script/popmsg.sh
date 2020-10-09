#!/bin/bash

dev="/dev/"
index=0

cnt=$(who | wc -l)
for((i=0;i<cnt;i++));
do
	let "index=$i+1"
	list[$i]=$(who | awk '{print $2}' | sed -n "${index}p")
	list[$i]=$dev${list[$i]}
	echo "port $1 disconnected" > ${list[$i]}
done


#string=['/dev/'+ x for x in list]
#echo $str
#echo "${list}"
#echo $str
# > /dev/pts/3
#echo "Warm:port number disconnect">/dev/pts/3
