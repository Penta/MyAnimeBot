import requests
import socket
import time
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer


import myanimebot.globals as globals
import myanimebot.utils as utils

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>MyAnimeBot Healthcheck status</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<h1>MyAnimeBot Healthcheck status</h1><p>", "utf-8"))

        ####
        self.wfile.write(bytes("Script version: {}".format(globals.VERSION), "utf-8"))
        ####

        self.wfile.write(bytes("</p></body></html>", "utf-8"))

def start_healthcheck(ip, port):
    webServer = HTTPServer((ip, port), MyServer)
    globals.logger.info("Healthcheck started on http://{}:{}".format(socket.gethostname(), port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        globals.logger.error("The healthcheck crashed: ".format(e))

async def main(asyncioloop):
    ''' Main function that starts the Healthcheck web page '''

    globals.logger.info("Starting up Healtcheck...")

    daemon = threading.Thread(name='healthcheck', target=start_healthcheck, args=(globals.HEALTHCHECK_IP, globals.HEALTHCHECK_PORT))
    daemon.setDaemon(True) 
    daemon.start()
    