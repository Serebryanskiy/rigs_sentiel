#!/usr/bin/env bash

# git clone https://github.com/Serebryanskiy/rigs.git
# cd rigs_sentinel
# Install requirements
sudo apt-get install -y build-essential
sudo apt-get install -y checkinstall
sudo apt-get install -y libreadline-gplv2-dev
sudo apt-get install -y libncursesw5-dev
sudo apt-get install -y libssl-dev
sudo apt-get install -y libsqlite3-dev
sudo apt-get install -y tk-dev
sudo apt-get install -y libgdbm-dev
sudo apt-get install -y libc6-dev
sudo apt-get install -y libbz2-dev
sudo apt-get install -y zlib1g-dev
sudo apt-get install -y openssl
sudo apt-get install -y libffi-dev
sudo apt-get install -y python3-dev
sudo apt-get install -y python3-setuptools
sudo apt-get install -y wget

# Prepare to build
mkdir /tmp/Python37
cd /tmp/Python37

# Pull down Python 3.7, build, and install
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar xvf Python-3.7.3.tar.xz
cd /tmp/Python37/Python-3.7.3
./configure
sudo make altinstall

# Install SQL
cd ~/tmp
wget https://dev.mysql.com/get/mysql-apt-config_0.8.13-1_all.deb
sudo dpkg -i mysql-apt-config_0.8.13-1_all.deb
sudo apt-get update
sudo apt-get install -y mysql-server

#Github get
install apt install -y git
cd
install -r requirements.txt
mysql -uroot  -p < createdb.sql
