pts=$(tty | cut -d '/' -f4)

#For console session
if [ -z "$pts" ]; then
  pts=$(tty | cut -d '/' -f3 | cut -d 'S' -f2)
fi

filename="pts"$pts".cfg"

#remove stale entries
rm -rf /tmp/pts$pts.cfg

#Create unique file entry for each tty
echo "interface_mode=DEFAULT" > /tmp/$filename
