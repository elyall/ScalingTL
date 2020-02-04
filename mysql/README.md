# [Setting up MySQL](https://support.rackspace.com/how-to/install-mysql-server-on-the-ubuntu-operating-system/)

Install MySQL, update firewall, bind database to IP, and start service
```
sudo apt-get install mysql-server
sudo service mysql start
sudo mysql_secure_installation utility
sudo ufw allow mysql
sudo ufw allow 'OpenSSH'
sudo ufw enable
sudo service mysql start
sudo systemctl enable mysql # enable at startup
nano /etc/mysql/mysql.conf.d/mysqld.cnf # change: bind-address = 0.0.0.0
sudo service mysql restart
```

Create MySQL user & database
```
sudo mysql -u root
```
```SQL
UPDATE mysql.user SET authentication_string = PASSWORD('NEW_ROOT_PASSWORD_HERE') WHERE User = 'root';
FLUSH PRIVILEGES;
SELECT User, Host, plugin, authentication_string FROM mysql.user; /* list users */

CREATE DATABASE metaflow;
SHOW DATABASES; /* list databases */

CREATE USER 'USERNAME_HERE'@'localhost' IDENTIFIED BY 'USER_PASSWORD_HERE';
CREATE USER 'USERNAME_HERE'@'%' IDENTIFIED BY 'USER_PASSWORD_HERE'; /* make user available remote */
GRANT ALL ON *.* to 'USERNAME_HERE'@'localhost';
GRANT ALL ON *.* TO 'USERNAME_HERE'@'%';
FLUSH PRIVILEGES;
```