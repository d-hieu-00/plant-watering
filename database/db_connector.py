# import psycopg2
import sqlite3
import sys
import pathlib
import json
# import mysql.connector

# Internal
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils.utils import logger

class DBConnector:
    PostgreSQL = "PostgreSQL"
    SQLite3 = "SQLite3"
    MariaDB = "MariaDB"
    @property
    def class_name(self): return self.__class__.__name__
    @property
    def db_type(self): return self.__db_type
    @property
    def db_config(self):
        if self.__db_config is None: return "{}"
        return json.dumps(self.__db_config)

    def __init__(self, db, config):
        self.__db_config = config
        self.__db_type = db
        logger.info(f"[{self.class_name}] Init db '{self.db_type}'", config)
        self.__verify_config()

    def __del__(self):
        logger.debug(f"[{self.class_name}] Deinit db '{self.db_type}', config: '{self.db_config}'")

        # self.DATABASE = sqlite3.connect(self.DATABASE_FILE_PATH, check_same_thread=False)
    def __new_connection(self):
        # if self.__db_type == self.PostgreSQL:
        #     return psycopg2.connect(**self.__db_config)
        if self.__db_type == self.SQLite3:
            return sqlite3.connect(self.__db_config["path"], check_same_thread=False)
        # elif self.__db_type == self.MariaDB:
        #     return mysql.connector.connect(**self.__db_config)
        else: raise Exception(f"[{self.class_name}] Not support db '{self.db_type}'")

    def __verify_config(self):
        ok = type(self.__db_config) == type({})
        if self.__db_type == self.PostgreSQL or self.__db_type == self.MariaDB:
            ok = ok \
             and self.__db_config.keys().__contains__("host") \
             and self.__db_config.keys().__contains__("database") \
             and self.__db_config.keys().__contains__("user") \
             and self.__db_config.keys().__contains__("password")
        elif self.__db_type == self.SQLite3:
            ok = ok and self.__db_config.keys().__contains__("path")
        if ok == False: raise Exception(f"[{self.class_name}] Invalid config for db '{self.db_type}'")
        try:
            db_conn = self.__new_connection()
            db_conn.close()
        except Exception as error:
            raise Exception(f"[{self.class_name}] Failed to connect to db '{self.db_type}', config: '{self.db_config}', error: '{str(error)}'")

    def new_connection(self):
        return self.__new_connection()
