## MySQL
# https://support.rackspace.com/how-to/install-mysql-server-on-the-ubuntu-operating-system/
sudo apt-get install mysql-server
sudo service mysql start
sudo mysql_secure_installation utility
sudo ufw enable
sudo ufw allow mysql
sudo service mysql start
sudo systemctl enable mysql
# /etc/mysql/mysql.conf.d/mysqld.cnf -> bind-address = 0.0.0.0
sudo service mysql restart

sudo mysql -u root
UPDATE mysql.user SET authentication_string = PASSWORD('uNw5^Hze6K&v24Z!PeCak*^n') WHERE User = 'root';
FLUSH PRIVILEGES;

SELECT User, Host, plugin, authentication_string FROM mysql.user; # list users

CREATE DATABASE metaflow;
SHOW DATABASES; # list databases

CREATE USER 'db_user'@'localhost' IDENTIFIED BY 'uNw5^Hze6K&v24Z!PeCak*^n';
CREATE USER 'db_user'@'%' IDENTIFIED BY 'uNw5^Hze6K&v24Z!PeCak*^n';
GRANT ALL ON *.* to 'db_user'@'localhost';
GRANT ALL ON *.* TO 'db_user'@'%';
FLUSH PRIVILEGES;