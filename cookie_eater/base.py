#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Part of the CookieEater package.
#
# Copyright (c) 2017 - Chris Griffith - MIT License
"""
Classes for managing Firefox and Chrome Cookies
"""

import os
import sqlite3
import datetime
import sys

from reusables import unique

__all__ = ['CookieManager', 'BrowserException', 'InvalidSchema',
           'MissingCookiesDB']


def _to_secs(td):
    """
    Compatibility for 2.6 and 3.2 for timedelta.total_seconds()

    :return: float of seconds
    """
    if (sys.version_info[0:2] < (2, 7) or
       (2, 7) < sys.version_info[0:2] < (3, 3)):
        return ((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 **
                6) / 10 ** 6)
    else:
        return td.total_seconds()


def get_platform():
    """
    Provides the common name of the platform the code is currently running on.

    :return: Platform name as str
    """
    if "linux" in sys.platform:
        return "linux"
    elif "darwin" in sys.platform:
        return "mac"
    elif sys.platform in ("win32", "cygwin"):
        return "windows"
    else:
        raise BrowserException("Unsupported Platform for"
                               " automation profile gathering")


class BrowserException(Exception):
    """Generic parent exception for errors in this module"""


class InvalidSchema(BrowserException):
    """The provided DB did not have a valid scheme"""


class MissingCookiesDB(BrowserException):
    """Could not find the Cookie DB"""


class CookieManager(object):
    """
    Parent class for all cookies managers for better cross browser
    compatibilities and portability.
    """
    _valid_structure = {"tables": [],
                        "columns": []}
    _db_paths = {
        "window": "",
        "mac": "",
        "linux": ""}
    _insert = ""
    db = ""
    table_name = ""

    def __init__(self, db=None):
        self.db = db if db else self.find_db()
        self.verify_schema()

    def _correct_tables_and_titles(self, cur):
        """
        Performs table and column name lookup and makes sure they match the
        defined valid schema.

        :param cur: SQLite cursor
        :type cur: sqlite3.Connection.cursor
        """

        grab_ts = cur.execute("SELECT name FROM sqlite_master "
                              "WHERE type = 'table'")
        tables = grab_ts.fetchall()
        grab_row = cur.execute("SELECT * FROM {0} LIMIT 1".format(
            self.table_name))
        cols = [description[0] for description in grab_row.description]

        if tables != self._valid_structure["tables"]:
            raise InvalidSchema("Tables expected {0} - Got {1}".format(
                self._valid_structure["tables"], tables))
        if cols != self._valid_structure["columns"]:
            raise InvalidSchema("Columns expected {0} - Got {1}".format(
                self._valid_structure["columns"], cols))

    def verify_schema(self):
        """
        Match the selected DB to the class's valid schema to verify
        compatibility. Raises InvalidSchema on error.
        """
        conn = sqlite3.Connection(self.db)
        cur = conn.cursor()
        try:
            self._correct_tables_and_titles(cur)
        finally:
            conn.close()

    def find_db(self):
        """
        Look at the default profile path based on system platform to
        find the browser's cookie database.

        :return: Path the cookie file in the default profile as str
        """
        cookies_path = os.path.expanduser(self._db_paths[get_platform()])

        cookies_path = self._find_db_extra(cookies_path)

        if not os.path.exists(cookies_path):
            raise MissingCookiesDB("Cookie does not exist at "
                                   "{0}".format(cookies_path))
        return cookies_path

    @staticmethod
    def _find_db_extra(expanded_path):
        """Some browser's profiles require path manipulation"""
        return expanded_path

    @unique(wait=1, exception=BrowserException,
            error_text="Could not generate unique timestamp")
    def _current_time(self, epoch=datetime.datetime(1970, 1, 1), length=16):
        """
        Returns a string of the current time based on epoc date at a set
         length of integers.
         """
        delta_from_epic = (datetime.datetime.utcnow() - epoch)
        return int(str(_to_secs(delta_from_epic)
                       ).replace(".", "")[:length].ljust(length, "0"))

    @staticmethod
    def _expire_time(epoch=datetime.datetime(1970, 1, 1), length=10,
                     expires_in=datetime.timedelta(days=1)):
        """
        Returns a string of time based on epoch date at a set
         length of integers with an additional timedelta as specified.
         """
        delta_from_epic = (datetime.datetime.utcnow() - epoch + expires_in)
        return int(str(_to_secs(delta_from_epic)
                       ).replace(".", "")[:length].ljust(length, "0"))

    def _connect(self):
        """
        Overrideable SQL connection
        function to return connection and cursor
        """
        conn = sqlite3.Connection(self.db)
        cur = conn.cursor()
        return conn, cur

    def _insert_command(self, cursor, host, name, value, path,
                        expires_at, secure, http_only, **kwargs):
        """Child class must override"""
        raise NotImplementedError()

    def _delete_command(self, cursor, host, name):
        """Child class must override"""
        raise NotImplementedError()

    def _limited_select_command(self, cursor):
        """Child class must override"""
        raise NotImplementedError()

    def _match_command(self, cursor, match, value):
        """Child class must override"""
        raise NotImplementedError()

    def _row_to_dict(self, row):
        """
        Child class must override.

        The dictionary must contain:
        - host
        - name
        - value
        """
        raise NotImplementedError()

    def _int_time_to_float(self, int_time, period_placement=10):
        """Turn integer based time from DBs into regular float time"""
        return float("{0}.{1}".format(str(int_time)[:period_placement],
                                      str(int_time)[period_placement:]))

    def add_cookie(self, host, name, value, path="/",
                   expires_in=datetime.timedelta(days=1), secure=0,
                   http_only=0, **kwargs):
        """
        Abstracted function to add a cookie to the database.
        Additional browser specific keyword arguments are availablee,
        listed in their respective classes.

        :param host: URL to associate cookie with
        :param name: The name of the cookie, such as "SESSIONID"
        :param value: the cookie content
        :param path: Defalt path is "/", some websites modify this
        :param expires_in: timedelta from now when cookies expires
        :param secure: 0 or 1 for to use on secured connections only
        :param http_only: 0 or 1 Use on http only
        """
        conn, cur = self._connect()
        try:
            self._insert_command(cur, host, name, value, path, expires_in,
                                 secure, http_only, **kwargs)
        except Exception as err:
            raise BrowserException(str(err))
        else:
            try:
                conn.commit()
            except Exception as err:
                raise BrowserException("Could not commit changes to database, "
                                       "is browser open? - {0}".format(err))
        finally:
            conn.close()

    def delete_cookie(self, host, name):
        """
        Abstracted function to remove a cookie from the database.

        :param host: URL of cookie, must be exact
        :param name: The name of the cookie, such as "SESSIONID"
        """
        conn, cur = self._connect()
        try:
            self._delete_command(cur, host, name)
        except Exception as err:
            raise BrowserException(str(err))
        else:
            try:
                conn.commit()
            except Exception as err:
                raise BrowserException("Could not commit changes to database, "
                                       "is browser open? - {0}".format(err))
        finally:
            conn.close()

    def update_cookie(self, host, name, value, path="/",
                      expires_in=datetime.timedelta(days=1),
                      secure=0, http_only=0, ignore_missing=True, **kwargs):
        """
        Delete and re-add a cookie with different value.

        :param host: URL to associate cookie with
        :param name: The name of the cookie, such as "SESSIONID"
        :param value: the cookie content
        :param path: Defalt path is "/", some websites modify this
        :param expires_in: timedelta from now when cookies expires
        :param secure: 0 or 1 for to use on secured connections only
        :param http_only: 0 or 1
        :param ignore_missing: Boolean, if set to False it will raise an
        exception if there is not a cookie to remove before updating
        """
        conn, cur = self._connect()

        try:
            self._delete_command(cur, host, name)
        except Exception as err:
            if not ignore_missing:
                raise BrowserException(str(err))

        try:
            self._insert_command(cur, host, name, value, path, expires_in,
                                 secure, http_only, **kwargs)
        except Exception as err:
            raise BrowserException(str(err))
        else:
            try:
                conn.commit()
            except Exception as err:
                raise BrowserException("Could not commit changes to database, "
                                       "is browser open? - {0}".format(err))
        finally:
            conn.close()

    def find_cookies(self, host="", name="", value=""):
        """
        Search for cookies based of the host, name or cookie contents.
        All values are loose, and will be compared by converting to lowercase
        and check if they exist "in" the field specified.

        :param host: Cookie URL to search
        :param name: The name of the cookie
        :param value: Search the contents of the cookie
        :return: list of cookies in dict form
        """
        if not host and not name and not value:
            raise BrowserException("Please specify something to search by")
        conn, cur = self._connect()

        try:
            rows = self._limited_select_command(cur)
        except Exception as err:
            conn.close()
            raise BrowserException(str(err))

        result_ids, results = list(), list()

        for row in rows:
            match = False
            if host and host.lower() in row[1].lower():
                match = True
            if name and name.lower() in row[2].lower():
                match = True
            if value and value.lower() in row[3].lower():
                match = True
            if match:
                result_ids.append(row[0])

        for result in result_ids:
            try:
                row = self._match_command(cur, "rowid", result)
            except Exception as err:
                conn.close()
                raise BrowserException(str(err))
            else:
                results.append(self._row_to_dict(row.fetchone()))
        conn.close()
        return results

    def dump(self):
        """
        Dump the database to a list of dictionaries.

        :return: list of every row from the Cookies database, as dictionaries
        """
        conn, cur = self._connect()

        try:
            rows = self._match_command(cur, 1, 1)
        except Exception as err:
            raise BrowserException(str(err))
        else:
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()
