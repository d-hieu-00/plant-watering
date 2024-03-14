from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from socketserver import ThreadingMixIn
import json, ssl
import threading, time
import signal
import os, random
import mimetypes
import re
import pathlib
from urllib.parse import parse_qs, urlparse

# Internal
import trained.model as model
from utils.utils import logger
from utils.utils import safe_execute
from database.db_connector import DBConnector

# logger.set_level(logger.DEBUG)
# logger.set_file("abc.log")

CERTIFICATE_PATH = ''
USE_TLS          = False
PORT             = 80
DB_NAME          = "plant-watering.db.sqlite"

class UtilsDB:
    def __init__(self, db_config = { "path": str(pathlib.Path(__file__).parent.joinpath(DB_NAME)) }):
        self.__connector = DBConnector(DBConnector.SQLite3, db_config)
        self.__rconn = self.__connector.new_connection()
        self.__wconn = self.__connector.new_connection()
        self.__wlock = threading.Lock()
        self.__create_tables()
        logger.info("Start Utils DB", db_config)

    def __del__(self):
        self.__wconn.close()
        self.__rconn.close()

    def __write(self, query: str, *args):
        logger.debug("Excute write query", query, *args)
        with self.__wlock:
            cursor = self.__wconn.cursor()
            cursor.execute(query, [*args])
            self.__wconn.commit()
            return True

    def __create_tables(self):
        logger.debug("Create monitor tables")
        queries = [
            """ CREATE TABLE IF NOT EXISTS err_log (
                time BIGINT NOT NULL PRIMARY KEY,
                data TEXT NOT NULL
            ) WITHOUT ROWID;
            """,
            """ CREATE TABLE IF NOT EXISTS data_process (
                time            BIGINT NOT NULL PRIMARY KEY,
                humidity        REAL NOT NULL,
                temp            REAL NOT NULL,
                soil_moisture   REAL NOT NULL,
                status          INT NOT NULL,
                action          INT NOT NULL
            ) WITHOUT ROWID;
            """,
            """ CREATE TABLE IF NOT EXISTS config (
                key  TEXT NOT NULL PRIMARY KEY,
                data TEXT DEFAULT '{}'
            ) WITHOUT ROWID;
            """,
        ]
        ok = True
        for query in queries:
            if ok != True: break
            ok = safe_execute(None, self.__write, query)

    def record_proc(self, humidity, temp, soil_moisture, status, action):
        query = "INSERT INTO data_process(time, humidity, temp, soil_moisture, status, action) VALUES (?, ?, ?, ?, ?, ?)"
        return safe_execute(None, self.__write, query, int(time.time() * 1000), humidity, temp, soil_moisture, status, action)

    def record_err(self, data):
        query = "INSERT INTO err_log(time, data) VALUES (?, ?)"
        return safe_execute(None, self.__write, query, int(time.time() * 1000), data)

    def save_conf(self, data):
        query = "INSERT INTO config(key, data) VALUES (?, ?)"
        return safe_execute(None, self.__write, query, 'base', data)

    def query_conf(self):
        query = "SELECT data FROM config where key = ?"
        cursor = self.__rconn.cursor()
        cursor.execute(query, 'base')
        _rows = cursor.fetchall()

        if len(_rows) == 0:
            return '{}'
        return json.dumps(_rows[0])

    def query_proc(self, start, end):
        query = "SELECT time, humidity, temp, soil_moisture, status, action FROM data_process "
        cond  = ""
        args  = []
        if start is not None:
            cond += "start >= ?"
            args.append(start)
        if end is not None:
            cond += "end <= ?"
            args.append(end)
        if cond != '':
            query += f"WHERE {cond}"

        cursor = self.__rconn.cursor()
        cursor.execute(query, args)
        _rows = cursor.fetchall()
        return json.dumps(_rows)

    def quey_err(self, start, end):
        query = "SELECT time, data FROM err_log "
        cond  = ""
        args  = []
        if start is not None:
            cond += "start >= ?"
            args.append(start)
        if end is not None:
            cond += "end <= ?"
            args.append(end)
        if cond != '':
            query += f"WHERE {cond}"

        cursor = self.__rconn.cursor()
        cursor.execute(query, args)
        _rows = cursor.fetchall()
        return json.dumps(_rows)

class Utils:
    model    = model.load()
    database = UtilsDB()

    def handle_data(in_data):
        # example: humidity=97.6&temp=50&status=0
        if re.match("^((\\w+)=([0-9.]+)&{0,1})*$", in_data) is None:
            logger.error("Invalid data recevied", input = in_data)
            Utils.database.record_err("Invalid data recevied '%s'" % in_data)
            return "-1"

        parsed_data = {}
        try:
            for item in in_data.split('&'):
                if item == "": continue
                key, value = item.split('=')
                if key in ['humidity', 'temp', 'soil_moisture', 'status']:
                    if key in ['humidity', 'temp', 'soil_moisture']:
                        value = float(value)
                    else:
                        value = int(value)
                    parsed_data[key] = value
                else:
                    raise ValueError("Only accept ['humidity', 'temp', 'soil_moisture', 'status']")
            if len(parsed_data) != 4:
                raise ValueError("Missing required data ['humidity', 'temp', 'soil_moisture', 'status']")

        except Exception as e:
            logger.error("Invalid data recevied", input = in_data, err = e)
            Utils.database.record_err(f"Invalid data recevied '{in_data}'. Error: {e}")
            return "-1"

        logger.info("Recevied data to action", data = parsed_data)
        try:
            resp = "%s" % (model.predict(Utils.model, [parsed_data["humidity"], parsed_data["soil_moisture"], parsed_data["temp"]]))
            Utils.database.record_proc(parsed_data["humidity"], parsed_data["temp"], parsed_data["soil_moisture"], parsed_data["status"], resp)
            return resp
        except Exception as e:
            logger.error("Failed to predict", input = in_data, err = e)
            Utils.database.record_err(f"Failed to predict '{in_data}'. Error: {e}")
            return "-1"

class ServerHandler(BaseHTTPRequestHandler):
    __web_dir  = os.path.join(os.getcwd(), 'web/dist')

    @property
    def __class_name(self): return self.__class__.__name__

    def log_message(self, format, *args):
        logger.info(self.__class_name, __msg = (format % args))

    def log_error(self, format, *args):
        logger.error(self.__class_name, __msg = (format % args))

    def log_request(self, code='-', size='-'):
        if isinstance(code, HTTPStatus): code = code.value
        # content_len = self.headers['Content-Length']
        # self.data_str = self.rfile.read(int(content_len if content_len is not None else 0))
        # if self.__data_string.__len__() != 0:
        #     logger.info(self.__class_name, self.address_string(), self.requestline, str(code), body = self.__data_string)
        # else:
        logger.info(self.__class_name, self.address_string(), self.requestline, str(code))

    def send_ok(self):
        self.send_response(200)
        self.end_headers()

    def do_METHOD(self, method):
        if method not in ('GET', 'POST', 'PUT'):
            self.send_error(403, "Method Not Allowed")
        elif method in ['POST', 'PUT'] and self.path.startswith('/api') == False:
            self.send_error(403, "Method Not Allowed (1)")
        else:
            self.send_error(403, "Method Not Allowed (2)")

    def do_POST(self):
        self.handle_api_request('POST')

    def do_PUT(self):
        self.handle_api_request('PUT')

    def do_GET(self):
        if self.path.startswith('/api'):
            self.handle_api_request('GET')
        else:
            self.handle_ui_request()

    def handle_api_request(self, method):
        if method == "POST" and urlparse(self.path).path == "/api/handle":
            data_str = (self.rfile.read(int(self.headers['content-length']))).decode('utf-8')
            msg = Utils.handle_data(data_str)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(msg.encode())
        elif method == "PUT" and urlparse(self.path).path == "/api/config":
            data_str = (self.rfile.read(int(self.headers['content-length']))).decode('utf-8')
            msg = Utils.database.save_conf(data_str)
            if msg is None:
                self.send_error(500, f"Failed to update config '{data_str}'")
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Save config success".encode())
        elif method == "GET" and urlparse(self.path).path == "/api/config":
            msg = Utils.database.query_conf()
            if msg is None:
                self.send_error(500, f"Failed to query config")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(msg.encode())
        elif method == "GET" and urlparse(self.path).path == "/api/data":
            params = parse_qs(urlparse(self.path).params)
            start = None
            end   = None
            try:
                if 'start' in params:
                    start = int(params['start'][0])
                if 'end' in params:
                    end = int(params['end'][0])
            except Exception as e:
                msg = f"Invalid data to query '{self.path}'"
                logger.error(msg)
                self.send_error(400, msg)
                return

            msg = Utils.database.query_proc(start, end)
            if msg is None:
                msg = f"Failed to query data '{self.path}'"
                logger.error(msg)
                self.send_error(500, msg)
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(msg.encode())
        elif method == "GET" and urlparse(self.path).path == "/api/log":
            params = parse_qs(urlparse(self.path).params)
            start = None
            end   = None
            try:
                if 'start' in params:
                    start = int(params['start'][0])
                if 'end' in params:
                    end = int(params['end'][0])
            except Exception as e:
                msg = f"Invalid data to query '{self.path}'"
                logger.error(msg)
                self.send_error(400, msg)
                return

            msg = Utils.database.quey_err(start, end)
            if msg is None:
                msg = f"Failed to query data '{self.path}'"
                logger.error(msg)
                self.send_error(500, msg)
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(msg.encode())
        else:
            self.send_error(403, f"Not Allowed '{self.path}'")

    def handle_ui_request(self):
        # Serve UI files
        _path = urlparse(self.path).path.lstrip('/')
        filename = os.path.join(self.__web_dir, _path)

        if os.path.isfile(filename) == False:
            filename = os.path.join(self.__web_dir, 'index.html')

        with open(filename, 'rb') as f:
            mimetype = mimetypes.guess_type(filename)
            self.send_response(200)
            if mimetype[0] is not None:
                self.send_header('Content-type', mimetype[0])
            else:
                self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run(server):
    logger.info('Server running on port %s' % PORT, use_tls = USE_TLS, cert_file = CERTIFICATE_PATH)
    server.serve_forever()

""" Handle signal """
running = True
server  = None
def signal_handler(sig, _):
    global server, running
    if server is not None:
        server.shutdown()
        logger.info("Recvice '%s', Shutdown server on port %s" % (str(signal.Signals(sig).name), PORT))

    if running == False:
        logger.warn("Recvice '%s', Force exit" % str(signal.Signals(sig).name))
        exit(1)
    else: running = False

# Register SIGINT
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    server = ThreadedHTTPServer(('', PORT), ServerHandler)
    if USE_TLS:
        server.socket = ssl.wrap_socket(
            server.socket, server_side = True,
            certfile    = CERTIFICATE_PATH,
            ssl_version = ssl.PROTOCOL_TLSv1_2)

    running_thread = threading.Thread(target=run, args=[server])
    running_thread.start()

    while running or running_thread.is_alive(): time.sleep(1)
    running_thread.join()
