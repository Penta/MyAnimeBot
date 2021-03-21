import myanimebot.globals as globals
import myanimebot.utils as utils

import psycopg2.extras

def create_cursor():
	if (globals.dbType.lower() == "mariadb") or (globals.dbType.lower() == "mysql") :
		cursor = globals.conn.cursor(buffered=True, dictionary=True)

	elif (globals.dbType.lower() == "postgresql") or (globals.dbType.lower() == "pgsql") or (globals.dbType.lower() == "posgres") :
		cursor = globals.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	return cursor
	
def insert_feed_db(feed, service : str):
	cursor = create_cursor()
	
	if (globals.dbType.lower() == "mariadb") or (globals.dbType.lower() == "mysql") :
		cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type, service) VALUES (FROM_UNIXTIME(%s), %s, %s, %s, NOW(), %s, %s)",
						(feed.date_publication.timestamp(),
						 feed.media.name,
						 feed.media.url,
						 feed.user.name,
						 feed.get_status_str(),
						 service))
	elif (globals.dbType.lower() == "postgresql") or (globals.dbType.lower() == "pgsql") or (globals.dbType.lower() == "posgres") :
		cursor.execute("INSERT INTO t_feeds (published, title, url, \"user\", found, type, service) VALUES (TO_TIMESTAMP(%s), %s, %s, %s, NOW(), %s, %s)",
						(feed.date_publication.timestamp(),
						 feed.media.name,
						 feed.media.url,
						 feed.user.name,
						 feed.get_status_str(),
						 service))
	
	globals.conn.commit()