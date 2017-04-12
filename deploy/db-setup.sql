DROP DATABASE IF EXISTS interact;
CREATE DATABASE temmpo_d CHARACTER SET UTF8;
CREATE USER temmpo@'%' IDENTIFIED BY 'notsosecret';
CREATE USER temmpo_a@'%' IDENTIFIED BY 'notsosecret_a';
GRANT SELECT, INSERT, UPDATE, DELETE ON interact_p.* TO temmpo@'%';
GRANT ALL PRIVILEGES ON interact_p.* TO temmpo_a@'%';

# Minimum MySQL security setting from mysql_secure_installation to allow development via remote server
DELETE FROM mysql.user WHERE User='';

FLUSH PRIVILEGES;