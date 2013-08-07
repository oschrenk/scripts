# !/bin/sh
# SSH SOCKS proxy script for Mac OS X

# Set PROXY_USER and PROXY_HOST
#
# If choosing not to set credentials as Environmental Variables, replace the values below for $PROXY_USER and $PROXY_HOST with genuine credentials.
# ie
# remoteuser='user'
# remoteproxy='example.com'

# Get the min and max system-available ports.
lowerport=`sysctl net.inet.ip.portrange.first | cut -d " " -f 2`
upperport=`sysctl net.inet.ip.portrange.last | cut -d " " -f 2`
localport=`jot -r 1 $lowerport $upperport`

remoteuser=$PROXY_USER
remoteproxy=$PROXY_HOST
remoteport="22"

usage(){
echo ""
echo "Usage: proxy [on|off|killall|shutdown|no_args]"
echo "Proxy is a proxy settings toggle script for OSX"
echo "Proxy initiates an SSH tunnel and then enables a Socks proxy"
}

unknown_input(){
echo "Unknown input, try again with different term"
}

get_proxy_state(){
  result=`networksetup -getsocksfirewallproxy Wi-Fi | head -1 | cut -d ' ' -f2`
  echo $result
}

proxy_on(){
  remote_ip_before=`curl -s http://curlmyip.com/`

  echo "Listening on localhost:$localport. Modifying network settings.."
  sudo networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 $localport off
  echo "Starting SSH session. Will run in background for 1 day."
  ssh -f tunnel -N -D localhost:$localport sleep 1d

  remote_ip_after=`curl -s -S --socks5 127.0.0.1:$localport http://curlmyip.com/`
  echo "Your remote ip before connecting through the proxy is $remote_ip_before"
  echo "Your remote ip after  connecting through the proxy is $remote_ip_after"
  echo "The http_proxy for the terminal has NOT been set."
}

proxy_off(){
  echo "Disabling proxy in network settings."
  sudo networksetup -setsocksfirewallproxystate Wi-Fi off
  echo "Done!"
}

kill_all(){
  pids=`ps -A | grep "ssh -f" | grep "sleep" | awk '{print $1}'`
  echo "Killing all running proxy connections."
  for pid in $pids
    do
  `kill -9 $pid`
  done
}

shutdown(){
  proxy_off
  kill_all
  echo "Proxy shutdown complete!"
}

toggle_state(){
  # result=`get_proxy_state`
  echo $(get_proxy_state) | grep -i 'y' >> /dev/null
  if [[ $? =~ 0 ]]; then
    shutdown
    echo "OFF"
  else
    proxy_on
    echo "ON"
  fi
}

case $1 in
"on")
  proxy_on
  ;;
"off")
  proxy_off
  ;;
"killall")
  kill_all
  ;;
"shutdown")
  shutdown
  ;;
"usage")
  usage
  ;;
"")
  toggle_state
  ;;
*)
  unknown_input
  usage
  ;;
esac