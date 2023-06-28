DROP DATABASE IF EXISTS temmpo_d;
CREATE DATABASE temmpo_d CHARACTER SET UTF8;
CREATE USER temmpo@'%' IDENTIFIED BY 'notsosecret';
CREATE USER temmpo_a@'%' IDENTIFIED BY 'notsosecret_a';
GRANT SELECT, INSERT, UPDATE, DELETE ON temmpo_d.* TO temmpo@'%';
GRANT ALL PRIVILEGES ON temmpo_d.* TO temmpo_a@'%';

# Minimum MySQL security setting from mysql_secure_installation to allow development via remote server
DELETE FROM mysql.user WHERE User='';

FLUSH PRIVILEGES;