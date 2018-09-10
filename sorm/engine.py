# coding: utf-8

from sqlite3 import connect
from typing import List
from sorm.objects import Base
from sorm.orm import Query, QuerySelect, QueryUpdate, QueryDelete


def create_connection(db_path=':memory:', echo=False):
    """
    Creates the connection to DB.
    :param db_path: :class:`str` - the path to DB file
    :param echo: :class:`bool` - print the query statements to console
    :return :class:`Connection`: the connection object
    """
    return Connection(db_path, echo)


class Connection:
    """sORM API object. Keeps connection to DB and routes the queries."""
    def __init__(self, db_path, echo):
        self.connection = connect(db_path, isolation_level=None)
        self.call_echo = echo

    def __del__(self):
        self.connection.rollback()
        self.connection.close()

    def cursor(self):
        """Returns a cursor for the connection."""
        return self.connection.cursor()

    def create_table(self, *args: List[Base]):
        """Creates a table in DB."""
        if not args:
            raise ValueError('There is no table to create!')
        for table_obj in args:
            Base.check_subclass(table_obj)
            table_obj.check_structure()
            self.execute(Query._get_table_creation_query_text(table_obj))

    def add(self, *args):
        """Inserts objects to DB."""
        if not args:
            raise ValueError('There is no object to add!')
        for inst in args:
            text, params = Query._get_insert_query_text(inst)
            self.execute(text, params)

    def update(self, table_obj):
        """Returns the QueryUpdate object. Which allows to update DB data."""
        return QueryUpdate(self, table_obj)

    def delete(self, table_obj):
        """Returns the QueryDelete object. Which allows to delete DB data."""
        if issubclass(table_obj, Base):
            return QueryDelete(self, table_obj)
        elif isinstance(table_obj, Base):
            QueryDelete.delete(self, table_obj)
        else:
            raise TypeError('{} - it does not seems like a subclass or an instance of the Base class.')

    def query(self, table_obj: Base):
        """Returns the QuerySelect object. Which allows to select data from DB."""
        return QuerySelect(self, table_obj, table_obj.get_column_names())

    def echo(self, text, params):
        """Allows to print the query texts."""
        if self.call_echo:
            print('{}\n{}'.format(text, params if params else '').strip())

    def execute(self, query_text: str, params: tuple=tuple()) -> tuple:
        """Executes the query texts."""
        with Cursor(self) as cursor:
            result = cursor.execute(query_text, params)
            self.echo(query_text, params)
            return tuple(row for row in result)


class Cursor:
    """
    Query context manager.
    The recommend usage is:
    >>> with Cursor(connection) as cursor:
    >>>     result = cursor.execute(query_text, params)
    """
    def __init__(self, connection: Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_val:
            raise exc_val

    def executescript(self, query_text):
        return self.cursor.executescript(query_text)

    def execute(self, query_text: str, params: tuple=tuple()):
        return self.cursor.execute(query_text, params)


if __name__ == '__main__':
    pass
