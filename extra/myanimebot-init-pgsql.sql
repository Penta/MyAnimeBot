
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

CREATE TABLE IF NOT EXISTS "t_users" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "mal_user" TEXT NOT NULL,
  "service" TEXT NOT NULL DEFAULT 'mal',
  "servers" TEXT DEFAULT NULL,
  "added" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "t_servers" (
  "id" INT PRIMARY KEY NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 ),
  "server" BIGINT NOT NULL,
  "channel" BIGINT DEFAULT NULL,
  "admin_group" TEXT DEFAULT NULL
);

CREATE OR REPLACE VIEW v_top         AS SELECT "user", COUNT("title") AS "total" FROM t_feeds GROUP BY "user" ORDER BY COUNT("title") DESC;
CREATE OR REPLACE VIEW v_totalfeeds  AS SELECT COUNT(0) AS "total" FROM "t_feeds";
CREATE OR REPLACE VIEW v_totalanimes AS SELECT COUNT(0) AS "total" from "t_animes";

CREATE OR REPLACE FUNCTION "sp_animecountperkeyword"(IN anime_var text, IN limit_var INT DEFAULT 100)
   RETURNS TABLE("title" TEXT, "total" INT)
   LANGUAGE 'sql'
    
AS $BODY$
SELECT "title", COUNT(0) AS "total"
   FROM "t_feeds"
   WHERE LOWER("title") LIKE '%' || LOWER(anime_var) || '%'
   GROUP BY "title"
   ORDER BY COUNT(id) DESC
   LIMIT limit_var;
$BODY$;

CREATE OR REPLACE FUNCTION "sp_usersperkeyword"(IN anime_var text, IN limit_var INT DEFAULT 100)
   RETURNS TABLE("user" TEXT, "total" INT)
   LANGUAGE 'sql'
   
AS $BODY$
SELECT "user", COUNT("title") AS "total"
   FROM "t_feeds"
   WHERE LOWER("title") LIKE '%' || LOWER(anime_var) || '%'
   GROUP BY "user"
   ORDER BY COUNT("title") DESC
   LIMIT limit_var;
$BODY$;
