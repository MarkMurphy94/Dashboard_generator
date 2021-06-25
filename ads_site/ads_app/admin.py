from django.contrib import admin
import sqlite3

# Register your models here.


class DatabaseHelper:
    """
    DatabaseHelper is an object that handles queries to the database.

    Keyword arguments:
        db_name -- the absolute path to the Django database
    """
    db_name = ""

    def __init__(self, file):
        self.db_name = file

    # region Connection Methods
    def get_connection(self, connection):
        """
        Return a connection to the sqlite3 database at self.db_name.

        Keyword arguments:
            connection -- a connection to the Django database or None.
        """
        if connection:
            return connection
        return sqlite3.connect(self.db_name)

    @staticmethod
    def close_connection(connection, cursor):
        """Close a database connection, as well as the associated cursor."""
        cursor.close()
        connection.close()

    # endregion Connection Methods

    # region Database Methods
    def get_user_id_by_user_name(self, user_name, connection=None, stay_connected=False):
        """
        Return a user's ID in the database. (int)

        Keyword arguments:
            user_name -- the name of a user
            connection -- a connection to the Django database
            stay_connected -- set to False to close connection after execution
        """
        conn = self.get_connection(connection)
        c = conn.cursor()

        c.execute(f'select id from auth_user where username=\'{user_name}\'')
        data = c.fetchone()

        if not stay_connected:
            self.close_connection(conn, c)
        return data[0]

    def get_group_id_by_group_name(self, group_name, connection=None, stay_connected=False):
        """
        Return a group's ID in the database. (int)

        Keyword arguments:
            group_name -- the name of a group
            connection -- a connection to the Django database
            stay_connected -- set to False to close connection after execution
        """
        conn = self.get_connection(connection)
        c = conn.cursor()

        c.execute(f'select id from auth_group where name=\'{group_name}\'')
        data = c.fetchone()

        if not stay_connected:
            self.close_connection(conn, c)
        return data[0]

    def get_group_name_by_group_id(self, group_id, connection=None, stay_connected=False):
        """
        Return a group's name in the database. (string)

        Keyword arguments:
            group_ids -- an array
            connection -- a connection to the Django database
            stay_connected -- set to False to close connection after execution
        """
        conn = self.get_connection(connection)
        c = conn.cursor()

        c.execute(f'select name from auth_group where id=\'{group_id}\'')
        data = c.fetchone()

        if not stay_connected:
            self.close_connection(conn, c)
        return data[0]

    def get_group_ids_by_user_name(self, user_name, connection=None, stay_connected=False):
        """
        Return an array containing all group IDs attached to a user. (int[])

        Keyword arguments:
            user_name -- the name of a user
            connection -- a connection to the Django database
            stay_connected -- set to False to close connection after execution
        """
        conn = self.get_connection(connection)
        c = conn.cursor()

        user_id = self.get_user_id_by_user_name(user_name, conn, stay_connected=True)
        c.execute(f'select group_id from auth_user_groups where user_id=\'{user_id}\'')
        data = c.fetchall()

        cleaned_data = []
        for row in data:
            cleaned_data.append(row[0])

        if not stay_connected:
            self.close_connection(conn, c)
        return cleaned_data

    # endregion Database Methods
