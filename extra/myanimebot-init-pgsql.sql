
-- Dumping structure for table myanimebot.t_animes
CREATE TABLE IF NOT EXISTS "t_animes" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "guid" TEXT NOT NULL,
  "service" TEXT NOT NULL DEFAULT 'mal',
  "title" TEXT DEFAULT NULL,
  "thumbnail" TEXT DEFAULT NULL,
  "found" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "discoverer" TEXT DEFAULT 'Anonymous',
  "media" TEXT DEFAULT 'unknown'
);


-- Dumping structure for table myanimebot.t_feeds
CREATE TABLE IF NOT EXISTS "t_feeds" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "published" TIMESTAMP NOT NULL,
  "title" TEXT DEFAULT NULL,
  "service" TEXT NOT NULL DEFAULT 'mal',
  "url" TEXT NOT NULL,
  "user" TEXT DEFAULT NULL,
  "found" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "type" TEXT DEFAULT 'N/A',
  "obsolete" INT NOT NULL DEFAULT 0
);

-- Dumping structure for table myanimebot.t_users
CREATE TABLE IF NOT EXISTS "t_users" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "mal_user" TEXT NOT NULL,
  "service" TEXT NOT NULL DEFAULT 'mal',
  "servers" TEXT DEFAULT NULL,
  "added" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dumping structure for table myanimebot.t_servers
CREATE TABLE IF NOT EXISTS "t_servers" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "server" BIGINT NOT NULL,
  "channel" BIGINT DEFAULT NULL,
  "admin_group" TEXT DEFAULT NULL
);

