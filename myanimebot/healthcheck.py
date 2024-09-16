import requests
import socket
import threading
import discord
import math

from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from tcp_latency import measure_latency


import myanimebot.globals as globals
import myanimebot.utils as utils
import myanimebot.anilist as anilist

webtext = ""
uptime = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):

        try:
            timestamp_request = datetime.now()
            webtext = "<html><head><title>MyAnimeBot Healthcheck status</title><link rel='icon' type='image/gif'' href='{}' /></head><body><h1>MyAnimeBot Healthcheck status</h1><table>".format(globals.iconBot)
            code = 200

            code, webtext = get_version(code, webtext)
            code, webtext = get_uptime(code, webtext)
            code, webtext = get_db_status(code, webtext)
            code, webtext = get_discord_websocket_status(code, webtext)
            code, webtext = get_anilist_status(code, webtext)
            code, webtext = get_myanimelist_status(code, webtext)

            generation_time = (datetime.now() - timestamp_request).total_seconds() * 1000
            webtext += "</table><p><em>Healthcheck generated in {}ms.</em></p></body></html>".format(round(generation_time))
        except:
            webtext = "<html><head><title>MyAnimeBot Healthcheck status</title></head><body><h1>MyAnimeBot Healthcheck status</h1><p>An unexpected error as occured when we tried to generate the healthcheck page, check the logs for more information.</p></body></html>"
            code = 503

            globals.logger.exception("Error on the healthcheck:\n")

        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(bytes(webtext, "utf-8"))


def line_formatter (desc : str, state : str, level : int):
    # Levels : 0 OK, 1 Error, 2 Warning, 3 Disabled

    if (level == 0):
        color = "7FFF00"
    elif (level == 1):
        color = "CD5C5C"
    elif (level == 2):
        color = "FFD700"
    else:
        color = "888888"

    result = "<tr><td>{}: </td><td bgcolor='{}' ><strong>{}</strong></td></tr>".format(desc, color, state)
    return result


def ping(hostname : str):
    latencies = measure_latency(host=hostname, runs=1, wait=0)
    total = 0

    for value in latencies:
        total += value

    result = math.trunc(total/len(latencies))
    return result


def get_anilist_status (code : int, webtext : str):
    if (globals.ANI_ENABLED):
        try:
            ani_status_code = requests.post(anilist.ANILIST_GRAPHQL_URL, timeout=3, allow_redirects=False).status_code

            if (ani_status_code == 400):
                ani_ping = ping("graphql.anilist.co")

                if (ani_ping < 300):
                    webtext += line_formatter("AniList API status", "OK ({}ms)".format(ani_ping), 0)
                else:
                    webtext += line_formatter("AniList API status", "SLOW ({}ms)".format(ani_ping), 2)
            else: 
                webtext += line_formatter("AniList API status", "KO ({})".format(ani_status_code), 1)
                if (code == 200): code = 500
        except Exception as e:
            webtext += line_formatter("AniList API status", "KO ({})".format(e), 1)
            if (code == 200): code = 500
    else:
        webtext += line_formatter("AniList API status", "DISABLED", 3)
    return code, webtext


def get_myanimelist_status (code : int, webtext : str):
    if (globals.MAL_ENABLED):
        try:
            mal_status_code = requests.head(globals.MAL_URL, timeout=3, allow_redirects=False).status_code

            if (mal_status_code == 200):
                mal_ping = ping("myanimelist.net")

                if (mal_ping < 300):
                    webtext += line_formatter("MyAnimeList status", "OK ({}ms)".format(mal_ping), 0)
                else:
                    webtext += line_formatter("MyAnimeList status", "SLOW ({}ms)".format(mal_ping), 2)
            else: 
                webtext += line_formatter("MyAnimeList status", "KO ({})".format(mal_status_code), 1)
                if (code == 200): code = 500
        except Exception as e:
            webtext += line_formatter("MyAnimeList status", "KO ({})".format(e), 1)
            if (code == 200): code = 500
    else:
        webtext += line_formatter("MyAnimeList status", "DISABLED", 3)
    return code, webtext


def get_uptime (code : int, webtext : str):
    webtext += line_formatter("Script uptime", uptime, 0)
    return code, webtext


def get_version (code : int, webtext : str):
    webtext += line_formatter("Script version", globals.VERSION, 0)
    return code, webtext


def get_discord_websocket_status (code : int, webtext : str):
    if (globals.client.is_closed()) or (not globals.client.is_ready()):
        webtext += line_formatter("Discord status", "KO", 1)
        if (code == 200): code = 500
    else:
        if (globals.client.is_ws_ratelimited()): webtext += line_formatter("Discord status", "NOT OK (Rate limited)", 2)
        else: webtext += line_formatter("Discord status", "OK (v{})".format(discord.__version__), 0)

    return code, webtext


def get_db_status (code : int, webtext : str):
    try:
        cursor = globals.conn.cursor(buffered=False)
        cursor.execute("SELECT * FROM t_feeds LIMIT 1;")
        cursor.fetchone()
        cursor.close()

        cursor = globals.conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT @@VERSION AS ver;")
        data = cursor.fetchone()
        cursor.close()

        webtext += line_formatter("Database status", "OK ({})".format(data["ver"]), 0)
    except Exception as e:
        webtext += line_formatter("Database status", "KO", 1)
        globals.logger.error("The healthcheck cannot access to the database: {}".format(e))
        if (code == 200): code = 500

    return code, webtext


def start_healthcheck(ip, port):
    webServer = HTTPServer((ip, port), MyServer)
    globals.logger.info("Healthcheck started on http://{}:{}".format(ip, port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        globals.logger.error("The healthcheck crashed: {}".format(e))

async def main(asyncioloop):
    ''' Main function that starts the Healthcheck web page '''

    globals.logger.info("Starting up Healtcheck...")

    healthcheck_thread = threading.Thread(name='healthcheck', target=start_healthcheck, args=(globals.HEALTHCHECK_IP, globals.HEALTHCHECK_PORT))
    healthcheck_thread.setDaemon(True) 
    healthcheck_thread.start()
    