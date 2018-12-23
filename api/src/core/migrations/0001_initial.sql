-- create tables

CREATE TABLE `access_tokens` (
  `user_id` int(11) NOT NULL,
  `access_token` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `browser` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `ip` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `expires` datetime NOT NULL,
  `permissions` text COLLATE utf8_unicode_ci,
  `lifetime` int(10) unsigned NOT NULL DEFAULT '300',
UNIQUE KEY `access_tokens_access_token_unique` (`access_token`),
KEY `access_tokens_user_id_index` (`user_id`)
) ENGINE=InnoDB;;

CREATE TABLE `login` (
  `success` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `ip` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;;

-- TODO remove obsolete tables (when not needed)
-- TODO DROP TABLE services;
-- TODO DROP TABLE relations;
-- TODO DROP TABLE migrations_apigateway
