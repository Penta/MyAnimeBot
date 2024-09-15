-- --------------------------------------------------------
-- Server version:               10.5.12-MariaDB-log - FreeBSD Ports
-- Server OS:                    FreeBSD12.2
-- HeidiSQL Version:             11.3.0.6295
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping structure for view myanimebot.check_DuplicateFeeds
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_DuplicateFeeds` (
	`published` DATETIME NOT NULL,
	`last seen` DATETIME NULL,
	`service` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`title` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci',
	`user` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_DuplicateMedia
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_DuplicateMedia` (
	`guid` MEDIUMTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`service` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`title` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_EmptyThumbnail
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_EmptyThumbnail` (
	`id` INT(11) UNSIGNED NOT NULL,
	`service` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`guid` MEDIUMTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`title` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci',
	`thumbnail` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci'
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_EventExecution
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_EventExecution` (
	`table` VARCHAR(64) NOT NULL COLLATE 'utf8_general_ci',
	`refreshed` DATETIME NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_Index
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_Index` (
	`table` VARCHAR(192) NOT NULL COLLATE 'utf8_general_ci',
	`index` VARCHAR(192) NOT NULL COLLATE 'utf8_general_ci',
	`read` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_OrphanMedias
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_OrphanMedias` (
	`id` INT(11) UNSIGNED NOT NULL,
	`service` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`media` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci'
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_TablesDiskUsage
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `check_TablesDiskUsage` (
	`table` VARCHAR(64) NOT NULL COLLATE 'utf8_general_ci',
	`dataMB` DECIMAL(24,2) NULL,
	`indexMB` DECIMAL(24,2) NULL,
	`totalMB` DECIMAL(25,2) NULL,
	`total` BIGINT(22) UNSIGNED NULL
) ENGINE=MyISAM;

-- Dumping structure for event myanimebot.event_generate_DailyAveragePerUser
DELIMITER //
CREATE EVENT `event_generate_DailyAveragePerUser` ON SCHEDULE EVERY 1 DAY STARTS '2020-01-05 01:30:00' ON COMPLETION PRESERVE ENABLE DO BEGIN

CALL spe_generate_DailyAveragePerUser;

END//
DELIMITER ;

-- Dumping structure for event myanimebot.event_generate_TopAnimes
DELIMITER //
CREATE EVENT `event_generate_TopAnimes` ON SCHEDULE EVERY 1 DAY STARTS '2019-12-08 05:00:00' ON COMPLETION PRESERVE ENABLE DO BEGIN

CALL spe_generate_TopAnimes;

END//
DELIMITER ;

-- Dumping structure for event myanimebot.event_generate_TopUniqueAnimePerUsers
DELIMITER //
CREATE EVENT `event_generate_TopUniqueAnimePerUsers` ON SCHEDULE EVERY 1 DAY STARTS '2019-11-05 05:00:00' ON COMPLETION PRESERVE ENABLE COMMENT 'Daily job' DO BEGIN

CALL spe_generate_TopUniqueAnimePerUsers;

END//
DELIMITER ;

-- Dumping structure for event myanimebot.event_generate_TotalDifferentAnimesPerUser
DELIMITER //
CREATE EVENT `event_generate_TotalDifferentAnimesPerUser` ON SCHEDULE EVERY 1 HOUR STARTS '2019-11-05 03:00:00' ON COMPLETION PRESERVE ENABLE COMMENT 'Daily job' DO BEGIN

CALL spe_generate_TotalDifferentAnimesPerUser;

END//
DELIMITER ;

-- Dumping structure for event myanimebot.event_history
DELIMITER //
CREATE EVENT `event_history` ON SCHEDULE EVERY 10 MINUTE STARTS '2019-11-15 00:00:00' ON COMPLETION PRESERVE ENABLE COMMENT 'Update the history table every 10 minutes' DO BEGIN

# Initialization of my time variable
SET @date = NOW();

# We get the values that we want to store
SELECT @totalFeeds          := total                  FROM v_TotalFeeds;
SELECT @totalUniqueFeeds    := COUNT(0)               FROM job_TopUniqueAnimePerUsers;
SELECT @totalMedia          := total                  FROM v_TotalAnimes;
SELECT @totalUsers          := COUNT(0)               FROM t_users;
SELECT @totalServers        := COUNT(0)               FROM t_servers;
SELECT @totalDuplicateFeeds := COUNT(0)               FROM check_DuplicateFeeds;
SELECT @totalDuplicateMedia := COUNT(0)               FROM check_DuplicateMedia;
SELECT @totalEmptyThumbnail := COUNT(0)               FROM check_EmptyThumbnail;
SELECT @totalInactiveUsers  := COUNT(0)               FROM v_ActiveUsers                 WHERE active = '0';
SELECT @spaceFeedsTable     := total                  FROM check_TablesDiskUsage         WHERE check_TablesDiskUsage.table = "t_feeds";
SELECT @spaceAnimesTable    := total                  FROM check_TablesDiskUsage         WHERE check_TablesDiskUsage.table = "t_animes";
SELECT @spaceUsersTable     := total                  FROM check_TablesDiskUsage         WHERE check_TablesDiskUsage.table = "t_users";
SELECT @spaceServersTable   := total                  FROM check_TablesDiskUsage         WHERE check_TablesDiskUsage.table = "t_servers";
SELECT @dailyAveragePerUser := ROUND(AVG(average), 3) FROM job_DailyAveragePerUser;
SELECT @totalOrphanMedias   := COUNT(0)               FROM check_OrphanMedias;
SELECT @nbMediaManga        := total                  FROM v_CountMediaType              WHERE v_CountMediaType.media = "manga";
SELECT @nbMediaAnime        := total                  FROM v_CountMediaType              WHERE v_CountMediaType.media = "anime";
SELECT @nbLog               := -1;
SELECT @nbErrorLog          := -1;

# We insert tour values
INSERT INTO t_history (date,  nbFeeds,     nbUniqueFeeds,     nbMedia,     nbUsers,     nbServers,     nbDuplicateFeeds,     nbDuplicateMedia,     nbEmptyThumbnail,     nbInactiveUsers,     spaceFeedsTable,  spaceAnimesTable,  spaceUsersTable,    spaceServersTable,  dailyAveragePerUser,  orphanMedias,       nbMediaManga,  nbMediaAnime,  nbLog,  nbErrorLog)
VALUES                (@date, @totalFeeds, @totalUniqueFeeds, @totalMedia, @totalUsers, @totalServers, @totalDuplicateFeeds, @totalDuplicateMedia, @totalEmptyThumbnail, @totalInactiveUsers, @spaceFeedsTable, @spaceAnimesTable, @spaceServersTable, @spaceServersTable, @dailyAveragePerUser, @totalOrphanMedias, @nbMediaManga, @nbMediaAnime, @nbLog, @nbErrorLog);

END//
DELIMITER ;

-- Dumping structure for event myanimebot.event_maintenance
DELIMITER //
CREATE EVENT `event_maintenance` ON SCHEDULE EVERY 1 DAY STARTS '2019-11-17 06:00:00' ON COMPLETION PRESERVE ENABLE COMMENT 'Executed at 6am, analyze the SQL tables' DO BEGIN

# Using the stored procedure.
CALL myanimebot.sp_Maintenance();

END//
DELIMITER ;

-- Dumping structure for table myanimebot.job_DailyAveragePerUser
CREATE TABLE IF NOT EXISTS `job_DailyAveragePerUser` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user` tinytext DEFAULT NULL,
  `average` decimal(24,4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user`(255))
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COMMENT='Autogenerated - Average daily medias per user';

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.job_TopAnimes
CREATE TABLE IF NOT EXISTS `job_TopAnimes` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `anime` mediumtext DEFAULT NULL,
  `nbUser` bigint(21) NOT NULL DEFAULT 0,
  `total` bigint(21) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_anime` (`anime`(768))
) ENGINE=InnoDB AUTO_INCREMENT=5640 DEFAULT CHARSET=utf8mb4 COMMENT='Autogenerated - Top listed animes and number of users';

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.job_TopUniqueAnimePerUsers
CREATE TABLE IF NOT EXISTS `job_TopUniqueAnimePerUsers` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user` tinytext DEFAULT NULL,
  `title` mediumtext DEFAULT NULL,
  `count` bigint(21) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user`(255)),
  KEY `idx_title` (`title`(768))
) ENGINE=InnoDB AUTO_INCREMENT=9629 DEFAULT CHARSET=utf8mb4 COMMENT='Autogenerated - Unique Anime feeds per users';

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.job_TotalDifferentAnimesPerUser
CREATE TABLE IF NOT EXISTS `job_TotalDifferentAnimesPerUser` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user` tinytext DEFAULT NULL,
  `total` bigint(21) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user`(255))
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COMMENT='Autogenerated - Total of different media per users';

-- Data exporting was unselected.

-- Dumping structure for procedure myanimebot.spe_generate_DailyAveragePerUser
DELIMITER //
CREATE PROCEDURE `spe_generate_DailyAveragePerUser`()
    SQL SECURITY INVOKER
BEGIN

# Create job_DailyAveragePerUser

# We drop the curent table
DROP TABLE IF EXISTS job_DailyAveragePerUser;

# We recreate the table with the current result of the view
CREATE TABLE job_DailyAveragePerUser IGNORE AS
	SELECT user, AVG(count) AS 'average'
	FROM (
		SELECT user, DATE(published) AS 'date', COUNT(*) AS 'count'
		FROM t_feeds
		WHERE DATE(published) != DATE(NOW())
		GROUP BY user, DATE
	) AS temp_DailyAveragePerUser
	GROUP BY user
	ORDER BY average DESC
;

# We apply the right configuration for the new table
ALTER TABLE job_DailyAveragePerUser
	COMMENT="Autogenerated - Average daily medias per user"
	COLLATE='utf8mb4_general_ci'
	ENGINE=InnoDB
;

# We create an ID column for the table
ALTER TABLE job_DailyAveragePerUser
	ADD COLUMN `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT FIRST,
	ADD PRIMARY KEY (`id`)
;

# We create indexes for the table
CREATE INDEX idx_user ON job_DailyAveragePerUser(user);

# And we analyze the created table
ANALYZE TABLE job_DailyAveragePerUser;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.spe_generate_TopAnimes
DELIMITER //
CREATE PROCEDURE `spe_generate_TopAnimes`()
    SQL SECURITY INVOKER
BEGIN

# Create job_TopAnimes

DROP TABLE IF EXISTS job_TopAnimes;

# We recreate the table with the current result of the view
CREATE TABLE job_TopAnimes AS SELECT * FROM v_TopAnimes;

# We apply the right configuration for the new table
ALTER TABLE job_TopAnimes
	COMMENT="Autogenerated - Top listed animes and number of users"
	COLLATE='utf8mb4_general_ci'
	ENGINE=InnoDB
;

# We create an ID column for the table
ALTER TABLE job_TopAnimes
	ADD COLUMN `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT FIRST,
	ADD PRIMARY KEY (`id`)
;

# We create indexes for the table
CREATE INDEX idx_anime ON job_TopAnimes(anime);

# And we analyze the created table
ANALYZE TABLE job_TopAnimes;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.spe_generate_TopUniqueAnimePerUsers
DELIMITER //
CREATE PROCEDURE `spe_generate_TopUniqueAnimePerUsers`()
    SQL SECURITY INVOKER
BEGIN

# Create job_TopUniqueAnimePerUsers

# We drop the curent table
DROP TABLE IF EXISTS job_TopUniqueAnimePerUsers;

# We recreate the table with the current result of the view
CREATE TABLE job_TopUniqueAnimePerUsers AS SELECT * FROM v_TopUniqueAnimePerUsers;

# We apply the right configuration for the new table
ALTER TABLE job_TopUniqueAnimePerUsers
	COMMENT="Autogenerated - Unique Anime feeds per users"
	COLLATE='utf8mb4_general_ci'
	ENGINE=InnoDB
;

# We create an ID column for the table
ALTER TABLE job_TopUniqueAnimePerUsers
	ADD COLUMN `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT FIRST,
	ADD PRIMARY KEY (`id`)
;

# We create indexes for the table
CREATE INDEX idx_user ON job_TopUniqueAnimePerUsers(user);
CREATE INDEX idx_title ON job_TopUniqueAnimePerUsers(title);

# And we analyze the created table
ANALYZE TABLE job_TopUniqueAnimePerUsers;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.spe_generate_TotalDifferentAnimesPerUser
DELIMITER //
CREATE PROCEDURE `spe_generate_TotalDifferentAnimesPerUser`()
    SQL SECURITY INVOKER
BEGIN

# Create job_TotalDifferentAnimesPerUser

# We drop the curent table
DROP TABLE IF EXISTS job_TotalDifferentAnimesPerUser;

# We recreate the table with the current result of the view
CREATE TABLE job_TotalDifferentAnimesPerUser AS SELECT * FROM v_TotalDifferentAnimesPerUser;

# We apply the right configuration for the new table
ALTER TABLE job_TotalDifferentAnimesPerUser
	COMMENT="Autogenerated - Total of different media per users"
	COLLATE='utf8mb4_general_ci'
	ENGINE=InnoDB
;

# We create an ID column for the table
ALTER TABLE job_TotalDifferentAnimesPerUser
	ADD COLUMN `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT FIRST,
	ADD PRIMARY KEY (`id`)
;

# We create indexes for the table
CREATE INDEX idx_user ON job_TotalDifferentAnimesPerUser(user);

# And we analyze the created table
ANALYZE TABLE job_TotalDifferentAnimesPerUser;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_AnimeCountPerKeyword
DELIMITER //
CREATE PROCEDURE `sp_AnimeCountPerKeyword`(
	IN `anime_var` TINYTEXT,
	IN `limit_var` INT
)
    SQL SECURITY INVOKER
    COMMENT 'Procédure pour récupèrer les statistiques d''animés répondant à un mot clef'
BEGIN

-- Default value is infinite for limit_var
IF limit_var = ''
THEN SET limit_var = '-1';
END IF;

-- Procedure to get animes statistics linked to a keyword

SELECT title AS 'title', COUNT(0) AS 'total'
   FROM t_feeds
   WHERE MATCH(title) AGAINST (anime_var)
   GROUP BY title
   ORDER BY COUNT(id) DESC
   LIMIT limit_var
;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_AnimesPerUser
DELIMITER //
CREATE PROCEDURE `sp_AnimesPerUser`(
	IN `user_var` TINYTEXT,
	IN `limit_var` INT
)
    SQL SECURITY INVOKER
    COMMENT 'Procédure pour récupèrer les statistiques d''animés sur un utilisateur'
BEGIN

-- Default value is infinite for limit_var
IF limit_var = ''
THEN SET limit_var = '-1';
END IF;

-- Procedure to get the statistics of user's animes
SELECT
  title AS "title",
  COUNT(title) AS "total"
FROM t_feeds
WHERE user = user_var
GROUP BY title
ORDER BY COUNT(title) DESC
LIMIT limit_var
;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_InitBoot
DELIMITER //
CREATE PROCEDURE `sp_InitBoot`()
    SQL SECURITY INVOKER
BEGIN

# Generate all event tables

CALL spe_generate_DailyAveragePerUser;
CALL spe_generate_TopAnimes;
CALL spe_generate_TopUniqueAnimePerUsers;
CALL spe_generate_TotalDifferentAnimesPerUser;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_Maintenance
DELIMITER //
CREATE PROCEDURE `sp_Maintenance`()
BEGIN

# Analyzing database's tables.
ANALYZE TABLE t_animes, t_feeds, t_history, t_servers, t_sys, t_users;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_RenameUser
DELIMITER //
CREATE PROCEDURE `sp_RenameUser`(
	IN `old_name_var` TINYTEXT,
	IN `new_name_var` TINYTEXT
)
    MODIFIES SQL DATA
    SQL SECURITY INVOKER
    COMMENT 'Rename a user in the database.'
BEGIN

-- Rename a user in the database.

-- For the table t_users
UPDATE t_users
	SET t_users.mal_user = new_name_var
	WHERE t_users.mal_user = old_name_var;

-- For the table t_animes
UPDATE t_animes
	SET t_animes.discoverer = new_name_var
	WHERE t_animes.discoverer = old_name_var;

-- For the table t_feeds
UPDATE t_feeds
	SET t_feeds.user = new_name_var
	WHERE t_feeds.user = old_name_var;


END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_TotalForKeyword
DELIMITER //
CREATE PROCEDURE `sp_TotalForKeyword`(
	IN `anime_var` TINYTEXT
)
    SQL SECURITY INVOKER
    COMMENT 'Total des animés répondants à un mot clef'
BEGIN

-- Total of animés that contains a specific keyword

SELECT COUNT(0) AS 'total'
   FROM t_feeds
   WHERE MATCH(title) AGAINST (anime_var)
;

END//
DELIMITER ;

-- Dumping structure for procedure myanimebot.sp_UsersPerKeyword
DELIMITER //
CREATE PROCEDURE `sp_UsersPerKeyword`(
	IN `anime_var` TINYTEXT,
	IN `limit_var` INT
)
    READS SQL DATA
    SQL SECURITY INVOKER
    COMMENT 'Statistiques des utilisateurs par rapport à un mot clef'
BEGIN

-- Default value is infinite for limit_var
IF limit_var = ''
THEN SET limit_var = '-1';
END IF;

-- Statistics of users according to a specific keyword
SELECT user AS 'user', COUNT(title) AS 'total'

   FROM t_feeds
   WHERE MATCH(title) AGAINST(anime_var)
   GROUP BY user
   ORDER BY COUNT(title) DESC
   LIMIT limit_var
;

END//
DELIMITER ;

-- Dumping structure for table myanimebot.t_animes
CREATE TABLE IF NOT EXISTS `t_animes` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `guid` mediumtext NOT NULL,
  `service` tinytext NOT NULL DEFAULT 'mal',
  `title` mediumtext DEFAULT NULL,
  `thumbnail` mediumtext DEFAULT NULL,
  `found` datetime NOT NULL DEFAULT current_timestamp(),
  `discoverer` tinytext DEFAULT 'Anonymous',
  `media` tinytext DEFAULT 'unknown',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_guid` (`guid`(768)) USING BTREE,
  KEY `idx_title` (`title`(768)),
  KEY `idx_discoverer` (`discoverer`(255)),
  KEY `idx_media` (`media`(255)),
  KEY `idx_service` (`service`(255)),
  FULLTEXT KEY `idx_title_str` (`title`)
) ENGINE=InnoDB AUTO_INCREMENT=5185 DEFAULT CHARSET=utf8mb4 AVG_ROW_LENGTH=224;

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.t_feeds
CREATE TABLE IF NOT EXISTS `t_feeds` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `published` datetime NOT NULL,
  `title` mediumtext DEFAULT NULL,
  `service` tinytext NOT NULL DEFAULT 'mal',
  `url` mediumtext NOT NULL,
  `user` tinytext DEFAULT NULL,
  `found` datetime NOT NULL DEFAULT current_timestamp(),
  `type` tinytext DEFAULT 'N/A',
  `obsolete` tinyint(3) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user`(255)),
  KEY `idx_title` (`title`(768)),
  KEY `idx_published` (`published`),
  KEY `idx_type` (`type`(255)),
  KEY `idx_service` (`service`(255)),
  FULLTEXT KEY `idx_title_str` (`title`)
) ENGINE=InnoDB AUTO_INCREMENT=29821 DEFAULT CHARSET=utf8mb4 AVG_ROW_LENGTH=172;

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.t_history
CREATE TABLE IF NOT EXISTS `t_history` (
  `date` datetime NOT NULL,
  `nbFeeds` int(11) unsigned NOT NULL DEFAULT 0,
  `nbUniqueFeeds` int(11) unsigned NOT NULL DEFAULT 0,
  `nbMedia` int(11) unsigned NOT NULL DEFAULT 0,
  `nbUsers` int(11) unsigned NOT NULL DEFAULT 0,
  `nbServers` int(11) unsigned NOT NULL DEFAULT 0,
  `nbDuplicateFeeds` int(11) unsigned NOT NULL DEFAULT 0,
  `nbDuplicateMedia` int(11) unsigned NOT NULL DEFAULT 0,
  `nbEmptyThumbnail` int(11) unsigned NOT NULL DEFAULT 0,
  `nbInactiveUsers` int(11) unsigned NOT NULL DEFAULT 0,
  `spaceFeedsTable` int(11) unsigned NOT NULL DEFAULT 0,
  `spaceAnimesTable` int(11) unsigned NOT NULL DEFAULT 0,
  `spaceUsersTable` int(11) unsigned NOT NULL DEFAULT 0,
  `spaceServersTable` int(11) unsigned NOT NULL DEFAULT 0,
  `dailyAveragePerUser` float unsigned NOT NULL DEFAULT 0,
  `orphanMedias` int(11) unsigned NOT NULL DEFAULT 0,
  `nbMediaManga` int(11) unsigned NOT NULL DEFAULT 0,
  `nbMediaAnime` int(11) unsigned NOT NULL DEFAULT 0,
  `nbLog` int(11) NOT NULL DEFAULT 0,
  `nbErrorLog` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`date`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='History of database';

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.t_servers
CREATE TABLE IF NOT EXISTS `t_servers` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `server` tinytext NOT NULL,
  `channel` tinytext DEFAULT NULL,
  `admin_group` tinytext DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_server` (`server`(255)) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 AVG_ROW_LENGTH=5461;

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.t_sys
CREATE TABLE IF NOT EXISTS `t_sys` (
  `param` tinytext NOT NULL,
  `value` text DEFAULT NULL,
  PRIMARY KEY (`param`(100)) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Data exporting was unselected.

-- Dumping structure for table myanimebot.t_users
CREATE TABLE IF NOT EXISTS `t_users` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `mal_user` tinytext NOT NULL,
  `service` tinytext NOT NULL DEFAULT 'mal',
  `servers` text DEFAULT NULL,
  `added` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_servers` (`servers`(768)),
  KEY `idx_service` (`service`(255)),
  KEY `idx_user` (`mal_user`(255)) USING BTREE,
  FULLTEXT KEY `idx_servers_str` (`servers`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 AVG_ROW_LENGTH=1820 COMMENT='Table where are stored the users of this bot.';

-- Data exporting was unselected.

-- Dumping structure for view myanimebot.v_ActiveUsers
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_ActiveUsers` (
	`user` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`service` TINYTEXT NOT NULL COLLATE 'utf8mb4_general_ci',
	`active` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_general_ci'
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_CountFeedsType
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_CountFeedsType` (
	`type` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_CountMediaType
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_CountMediaType` (
	`media` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_DailyHistory
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_DailyHistory` (
	`date` DATE NULL,
	`nbFeeds` INT(11) UNSIGNED NULL,
	`nbUniqueFeeds` INT(11) UNSIGNED NULL,
	`nbMedia` INT(11) UNSIGNED NULL,
	`nbUsers` INT(11) UNSIGNED NULL,
	`nbServers` INT(11) UNSIGNED NULL,
	`nbDuplacteFeeds` DECIMAL(12,0) NULL,
	`nbDuplicateMedia` DECIMAL(12,0) NULL,
	`nbEmptyThumbnail` DECIMAL(12,0) NULL,
	`nbInactiveUsers` DECIMAL(12,0) NULL,
	`spaceFeedsTable` DECIMAL(12,0) NULL,
	`spaceAnimesTable` DECIMAL(12,0) NULL,
	`SpaceUsersTable` DECIMAL(12,0) NULL,
	`SpaceServersTable` DECIMAL(12,0) NULL,
	`dailyAveragePerUser` DOUBLE(17,0) NULL,
	`orphanMedias` DECIMAL(12,0) NULL,
	`nbMediaManga` DECIMAL(12,0) NULL,
	`nbMediaAnime` DECIMAL(12,0) NULL,
	`nbLog` DECIMAL(11,0) NULL,
	`nbErrorLog` DECIMAL(11,0) NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_Top
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_Top` (
	`user` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_TopAnimes
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_TopAnimes` (
	`anime` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci',
	`nbUser` BIGINT(21) NOT NULL,
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_TopUniqueAnimePerUsers
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_TopUniqueAnimePerUsers` (
	`user` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`title` MEDIUMTEXT NULL COLLATE 'utf8mb4_general_ci',
	`count` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_TotalAnimes
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_TotalAnimes` (
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_TotalDifferentAnimesPerUser
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_TotalDifferentAnimesPerUser` (
	`user` TINYTEXT NULL COLLATE 'utf8mb4_general_ci',
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.v_TotalFeeds
-- Creating temporary table to overcome VIEW dependency errors
CREATE TABLE `v_TotalFeeds` (
	`total` BIGINT(21) NOT NULL
) ENGINE=MyISAM;

-- Dumping structure for view myanimebot.check_DuplicateFeeds
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_DuplicateFeeds`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_DuplicateFeeds` AS select `t_feeds`.`published` AS `published`,max(`t_feeds`.`found`) AS `last seen`,`t_feeds`.`service` AS `service`,`t_feeds`.`title` AS `title`,`t_feeds`.`user` AS `user`,count(0) AS `total` from `t_feeds` group by `t_feeds`.`published`,`t_feeds`.`title`,`t_feeds`.`user` having count(0) > 1;

-- Dumping structure for view myanimebot.check_DuplicateMedia
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_DuplicateMedia`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_DuplicateMedia` AS select `t_animes`.`guid` AS `guid`,`t_animes`.`service` AS `service`,`t_animes`.`title` AS `title`,count(0) AS `total` from `t_animes` group by `t_animes`.`guid`,`t_animes`.`title` having count(0) > 1;

-- Dumping structure for view myanimebot.check_EmptyThumbnail
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_EmptyThumbnail`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_EmptyThumbnail` AS select `t_animes`.`id` AS `id`,`t_animes`.`service` AS `service`,`t_animes`.`guid` AS `guid`,`t_animes`.`title` AS `title`,`t_animes`.`thumbnail` AS `thumbnail` from `t_animes` where `t_animes`.`thumbnail` = '' or `t_animes`.`thumbnail` is null;

-- Dumping structure for view myanimebot.check_EventExecution
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_EventExecution`;
CREATE ALGORITHM=MERGE SQL SECURITY DEFINER VIEW `check_EventExecution` AS select `information_schema`.`TABLES`.`TABLE_NAME` AS `table`,`information_schema`.`TABLES`.`CREATE_TIME` AS `refreshed` from `information_schema`.`TABLES` where `information_schema`.`TABLES`.`TABLE_NAME` like 'job\\_%' and `information_schema`.`TABLES`.`TABLE_SCHEMA` = 'myanimebot';

-- Dumping structure for view myanimebot.check_Index
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_Index`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_Index` AS select `information_schema`.`INDEX_STATISTICS`.`TABLE_NAME` AS `table`,`information_schema`.`INDEX_STATISTICS`.`INDEX_NAME` AS `index`,`information_schema`.`INDEX_STATISTICS`.`ROWS_READ` AS `read` from `information_schema`.`INDEX_STATISTICS` where `information_schema`.`INDEX_STATISTICS`.`TABLE_SCHEMA` = 'myanimebot' and `information_schema`.`INDEX_STATISTICS`.`INDEX_NAME` <> 'PRIMARY' order by `information_schema`.`INDEX_STATISTICS`.`ROWS_READ` desc;

-- Dumping structure for view myanimebot.check_OrphanMedias
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_OrphanMedias`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_OrphanMedias` AS select `t_animes`.`id` AS `id`,`t_animes`.`service` AS `service`,`t_animes`.`title` AS `media` from `t_animes` where !exists(select distinct `t_feeds`.`title` from `t_feeds` where `t_feeds`.`title` = `t_animes`.`title` limit 1);

-- Dumping structure for view myanimebot.check_TablesDiskUsage
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `check_TablesDiskUsage`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `check_TablesDiskUsage` AS select `information_schema`.`TABLES`.`TABLE_NAME` AS `table`,round(`information_schema`.`TABLES`.`DATA_LENGTH` / 1024 / 1024,2) AS `dataMB`,round(`information_schema`.`TABLES`.`INDEX_LENGTH` / 1024 / 1024,2) AS `indexMB`,round((`information_schema`.`TABLES`.`DATA_LENGTH` + `information_schema`.`TABLES`.`INDEX_LENGTH`) / 1024 / 1024,2) AS `totalMB`,`information_schema`.`TABLES`.`DATA_LENGTH` + `information_schema`.`TABLES`.`INDEX_LENGTH` AS `total` from `INFORMATION_SCHEMA`.`TABLES` where `information_schema`.`TABLES`.`TABLE_SCHEMA` = 'myanimebot' and `information_schema`.`TABLES`.`TABLE_TYPE` = 'BASE TABLE' and (`information_schema`.`TABLES`.`TABLE_NAME` like 't\\_%' or `information_schema`.`TABLES`.`TABLE_NAME` like 'job\\_%') order by `information_schema`.`TABLES`.`TABLE_NAME`;

-- Dumping structure for view myanimebot.v_ActiveUsers
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_ActiveUsers`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_ActiveUsers` AS select `t_users`.`mal_user` AS `user`,`t_users`.`service` AS `service`,case when exists(select 1 from `t_feeds` where `t_feeds`.`user` = `t_users`.`mal_user` limit 1) then '1' else '0' end AS `active` from `t_users`;

-- Dumping structure for view myanimebot.v_CountFeedsType
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_CountFeedsType`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_CountFeedsType` AS select `t_feeds`.`type` AS `type`,count(`t_feeds`.`id`) AS `total` from `t_feeds` where `t_feeds`.`type` <> 'N/A' group by `t_feeds`.`type` order by count(`t_feeds`.`id`) desc;

-- Dumping structure for view myanimebot.v_CountMediaType
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_CountMediaType`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_CountMediaType` AS select `t_animes`.`media` AS `media`,count(`t_animes`.`media`) AS `total` from `t_animes` group by `t_animes`.`media`;

-- Dumping structure for view myanimebot.v_DailyHistory
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_DailyHistory`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_DailyHistory` AS select cast(`t_history`.`date` as date) AS `date`,max(`t_history`.`nbFeeds`) AS `nbFeeds`,max(`t_history`.`nbUniqueFeeds`) AS `nbUniqueFeeds`,max(`t_history`.`nbMedia`) AS `nbMedia`,max(`t_history`.`nbUsers`) AS `nbUsers`,max(`t_history`.`nbServers`) AS `nbServers`,round(avg(`t_history`.`nbDuplicateFeeds`),0) AS `nbDuplacteFeeds`,round(avg(`t_history`.`nbDuplicateMedia`),0) AS `nbDuplicateMedia`,round(avg(`t_history`.`nbEmptyThumbnail`),0) AS `nbEmptyThumbnail`,round(avg(`t_history`.`nbInactiveUsers`),0) AS `nbInactiveUsers`,round(avg(`t_history`.`spaceFeedsTable`),0) AS `spaceFeedsTable`,round(avg(`t_history`.`spaceAnimesTable`),0) AS `spaceAnimesTable`,round(avg(`t_history`.`spaceUsersTable`),0) AS `SpaceUsersTable`,round(avg(`t_history`.`spaceServersTable`),0) AS `SpaceServersTable`,round(avg(`t_history`.`dailyAveragePerUser`),0) AS `dailyAveragePerUser`,round(avg(`t_history`.`orphanMedias`),0) AS `orphanMedias`,round(avg(`t_history`.`nbMediaManga`),0) AS `nbMediaManga`,round(avg(`t_history`.`nbMediaAnime`),0) AS `nbMediaAnime`,round(avg(`t_history`.`nbLog`),0) AS `nbLog`,round(avg(`t_history`.`nbErrorLog`),0) AS `nbErrorLog` from `t_history` group by cast(`t_history`.`date` as date) order by cast(`t_history`.`date` as date) desc;

-- Dumping structure for view myanimebot.v_Top
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_Top`;
CREATE ALGORITHM=TEMPTABLE SQL SECURITY INVOKER VIEW `v_Top` AS select `t_feeds`.`user` AS `user`,count(`t_feeds`.`title`) AS `total` from `t_feeds` group by `t_feeds`.`user` order by count(`t_feeds`.`title`) desc;

-- Dumping structure for view myanimebot.v_TopAnimes
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_TopAnimes`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_TopAnimes` AS select `t_feeds`.`title` AS `anime`,count(distinct `t_feeds`.`user`) AS `nbUser`,count(0) AS `total` from `t_feeds` group by `t_feeds`.`title` order by count(0) desc;

-- Dumping structure for view myanimebot.v_TopUniqueAnimePerUsers
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_TopUniqueAnimePerUsers`;
CREATE ALGORITHM=TEMPTABLE SQL SECURITY INVOKER VIEW `v_TopUniqueAnimePerUsers` AS select `t_feeds`.`user` AS `user`,`t_feeds`.`title` AS `title`,count(`t_feeds`.`title`) AS `count` from `t_feeds` group by `t_feeds`.`title`,`t_feeds`.`user` order by count(`t_feeds`.`title`) desc;

-- Dumping structure for view myanimebot.v_TotalAnimes
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_TotalAnimes`;
CREATE ALGORITHM=TEMPTABLE SQL SECURITY INVOKER VIEW `v_TotalAnimes` AS select count(0) AS `total` from `t_animes`;

-- Dumping structure for view myanimebot.v_TotalDifferentAnimesPerUser
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_TotalDifferentAnimesPerUser`;
CREATE ALGORITHM=TEMPTABLE SQL SECURITY INVOKER VIEW `v_TotalDifferentAnimesPerUser` AS select `t_feeds`.`user` AS `user`,count(distinct `t_feeds`.`title`) AS `total` from `t_feeds` group by `t_feeds`.`user` order by count(distinct `t_feeds`.`title`) desc;

-- Dumping structure for view myanimebot.v_TotalFeeds
-- Removing temporary table and create final VIEW structure
DROP TABLE IF EXISTS `v_TotalFeeds`;
CREATE ALGORITHM=TEMPTABLE SQL SECURITY INVOKER VIEW `v_TotalFeeds` AS select count(0) AS `total` from `t_feeds`;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;