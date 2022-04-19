#! /bin/bash

message="
 ERPAdda VM (built on `date +\"%B %d, %Y\"`)

 Please access ERPAdda by going to http://localhost:8080 on the host system.
 The username is \"Administrator\" and password is \"admin\"

 Consider buying professional support from us at https://erpadda.com/support 

 To update, login as
 username: vmraid
 password: vmraid
 cd vmraid-chair
 chair update
"
echo "$message" | sudo tee -a /etc/issue
echo "$message" | sudo tee -a /etc/motd
