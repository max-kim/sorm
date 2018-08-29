# coding: utf-8

from sys import exit


class NoTraceBackError(Exception):
    def __init__(self, msg):
        self.args = "{0.__name__}: {1}".format(type(self), msg),
        exit(self)


class ColumnIsNotFoundError(NoTraceBackError):
    pass


class TableDoesNotExist(NoTraceBackError):
    pass


class QueryError(NoTraceBackError):
    pass


class StructureError(NoTraceBackError):
    pass


class ColumnTypeError(NoTraceBackError):
    pass
