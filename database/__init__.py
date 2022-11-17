"""SQLite database interface."""

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
        """Record album in db.

        Args:
            gid (str): Google Photos album id
            name (str): Human readable name of album

        Returns:
            int: database incremental id of inserted row
        """
        return self._modify(
            'insert_album',
            {
                'gid': gid,
                'name': name
            }
        )

    def select_albums(self):
        """Return all rows of albums table.

        Returns:
            list[sqlite3.Rows]: all album rows
        """
        return self._select(
            'select_albums'
        )

    def select_album(self, album_id):
        """Find album by id.

        Args:
            id (int): database incremental id of album to find

        Returns:
            sqlite3.Row: Matching album
        """
        return self._select(
            'select_album_by_id',
            {
                'id': album_id
            },
            single=True
        )

    def insert_uploads(self, uploads):
        """Record uploads sent to API.

        Args:
            uploads (list[dict]):
                - album_id (int): db id of album
                - local_dir (str): directory file is in
                - filename (str): filename minus directory
                - media_id (str): remote id of item
        """
        self._modify(
            'insert_bulk_uploads',
            [
                {
                    'album_id': x['album_id'],
                    'local_dir': x['local_dir'],
                    'filename': x['filename'],
                    'media_id': x['media_id']
                }
                for x in uploads
            ]
        )

    def select_uploads(self, local_dir, album_id):
        """Get uploads already sent.

        Args:
            local_dir (str): folder on disk sent from
            aldum_id (int): db id of album sent into

        Returns:
            list[sqlite3.Row]: rows from uploads table
        """
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

    def _select(self, query, placeholders={}, single=False):
        cursor = self.connection.cursor()
        cursor.execute(
            self.queries[query],
            placeholders
        )
        if single:
            return cursor.fetchone()
        else:
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
