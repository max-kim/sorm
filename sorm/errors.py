# coding: utf-8

from sys import exc_info, exit
from inspect import currentframe


class NoTraceBackError(Exception):
    """
    The sORM errors base class. Allows to raise errors without traceback
    :param msg: (:class: `str`) - the error message
    """
    def __init__(self, msg):
        try:
            line_num = exc_info()[-1].tb_lineno
        except AttributeError:
            line_num = currentframe().f_back.f_lineno
        self.args = "{0.__name__}: ({1}) {2}".format(type(self), line_num, msg),
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
