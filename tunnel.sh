# !/bin/sh
# SSH SOCKS proxy script for Mac OS X

local_port=`jot -r 1 2000 65000`

if [ $1 == "on" ]; then
  echo "Listening on localhost:$local_port. Modifying network settings.."
  sudo networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 $local_port off
  echo "Starting SSH session. Will run in background for 1 day."
  ssh -f tunnel -N -D localhost:$local_port sleep 1d
fi

if [ $1 == "off" ]; then
  echo "Disabling proxy in network settings."
  sudo networksetup -setsocksfirewallproxystate Wi-Fi off
  echo "Done!"
fi

if [ $1 == "killall" ]; then
  pids=`ps -A | grep "ssh -f" | grep "sleep" | awk '{print $1}'`
  echo "Killing all running proxy connections."
  for pid in $pids
    do
  `kill -9 $pid`
  done
fi