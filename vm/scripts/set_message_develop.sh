#! /bin/bash

message="
 ERPAdda Evaluation VM (built on `date +\"%B %d, %Y\"`)

 Please access ERPAdda by going to http://localhost:8000 on the host system.
 The username is \"Administrator\" and password is \"admin\"

 Do consider donating at https://vmraid.io/buy

 To update, login as
 username: vmraid
 password: vmraid
 cd vmraid-chair
 chair update
"
echo "$message" | sudo tee -a /etc/issue
echo "$message" | sudo tee -a /etc/motd
