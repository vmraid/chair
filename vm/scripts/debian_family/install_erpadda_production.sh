#!/bin/bash -eux

# Install ERPAdda
wget https://raw.githubusercontent.com/vmraid/chair/develop/install.py
python install.py --production --user vmraid --mysql-root-password vmraid --admin-password admin