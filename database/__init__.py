"""SQLite database interface."""

import json
import os
import sqlite3


class DB(object):
    """Instance of DB interface."""

    connection = None
    queries = {}

    def __init__(self, filename):
        """Initialize db interface.

        Args:
            filename (str): sqlite database file

        """
        self.connection = sqlite3.connect(filename)
        self.connection.row_factory = sqlite3.Row

        # load query templates in dir, map filename to contents
        sql_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'queries'
        )
        self.queries = {
            x.replace('.sql', ''): open(os.path.join(sql_dir, x), 'r').read()
            for x in os.listdir(sql_dir)
            if x.endswith('.sql')
        }

        # run setup script
        self._script(self.queries['setup'])
        del self.queries['setup']

    def insert_album(self, gid, name):
        return self._modify(
            'insert_album',
            {
                'gid': gid,
                'name': name
            }
        )

    def select_albums(self):
        return self._select(
            'select_albums'
        )

    def select_album(self, album_id):
        return self._select(
            'select_album_by_id',
            {
                'id': album_id
            }
        )

    def insert_uploads(self, uploads):
        self._modify(
            'insert_bulk_uploads',
            [
                {
                    'album_id': x['album_id'],
                    'local_dir': x['local_dir'],
                    'filename': x['filename'],
                    'success': x['success']
                }
                for x in uploads
            ]
        )

    def select_uploads(self, local_dir, album_id):
        return self._select(
            'select_uploads_by_pair',
            {
                'local_dir': local_dir,
                'album_id': album_id
            }
        )

    def _script(self, queries):
        cursor = self.connection.cursor()
        cursor.executescript(queries)

    def _select(self, query, placeholders={}):
        cursor = self.connection.cursor()
        cursor.execute(
            self.queries[query],
            placeholders
        )
        return cursor.fetchall()

    def _modify(self, query, placeholders):
        cursor = self.connection.cursor()
        if type(placeholders) == list:
            cursor.executemany(
                self.queries[query],
                placeholders
            )
        else:
            cursor.execute(
                self.queries[query],
                placeholders
            )
        self.connection.commit()
        return cursor.lastrowid
