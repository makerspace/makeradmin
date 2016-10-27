CREATE USER `internal`@'localhost' IDENTIFIED BY 'g34Api5C9L';
CREATE DATABASE `internal`;
GRANT ALL ON `internal`.* TO `internal`@'localhost';
FLUSH PRIVILEGES;
