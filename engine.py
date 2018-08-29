# coding: utf-8

from sqlite3 import connect
from typing import List
from sorm.objects import Base
from sorm.orm import Query, QuerySelect, QueryUpdate, QueryDelete


def create_connection(db_path=':memory:', echo=False):
    return Connection(db_path, echo)


class Connection:
    def __init__(self, db_path, echo):
        self.connection = connect(db_path, isolation_level=None)
        self.call_echo = echo

    def __del__(self):
        self.connection.rollback()
        self.connection.close()

    def cursor(self):
        return self.connection.cursor()

    def create_table(self, *args: List[Base]):
        if not args:
            raise ValueError('There is no table to create!')
        for table_obj in args:
            if not issubclass(table_obj, Base):
                raise ValueError('{} does not seem like subclass of Base!'.format(table_obj.__name__))
            table_obj.check_structure()
            self.execute(Query._get_table_creation_query_text(table_obj))

    def add(self, *args):
        if not args:
            raise ValueError('There is no object to add!')
        for inst in args:
            text, params = Query._get_insert_query_text(inst)
            self.execute(text, params)

    def update(self, table_obj):
        return QueryUpdate(self, table_obj)

    def delete(self, table_obj):
        if type(table_obj) is type:
            return QueryDelete(self, table_obj)
        else:
            QueryDelete.delete(self, table_obj)

    def query(self, table_obj: Base, fields: str=''):
        if not issubclass(table_obj, Base):
            raise ValueError('{} does not seem like subclass of Base!'.format(table_obj.__name__))
        if fields:
            fields = table_obj.parse_column_names(fields)
        else:
            fields = table_obj.get_column_names()
        return QuerySelect(self, table_obj, fields)

    def echo(self, text, params):
        if self.call_echo:
            print('{}\n{}'.format(text, params if params else '').strip())

    def execute(self, query_text: str, params: tuple=tuple()) -> tuple:
        with Cursor(self) as cursor:
            result = cursor.execute(query_text, params)
            self.echo(query_text, params)
            return tuple(row for row in result)


class Cursor:
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
