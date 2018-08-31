# coding: utf-8

from sorm.errors import ColumnTypeError


class ForeignKey:
    """Allows to implement one to many relation.
    Performs the auto left join within select query.
    """
    def __init__(self, bound_class, bound_attr: str):
        self.bound_class = bound_class
        self.bound_attr = bound_attr
        self.self_type = None

    def __repr__(self):
        return 'FOREIGN KEY ({}) REFERENCES {} ({})'.format(self.self_type.col_name,
                                                            self.bound_class.table_name(),
                                                            self.bound_attr)


class NullType:
    """Superclass for data types. Implements the common functionality."""
    _prototype = 'NULL'
    _supported_operators = ['is', 'not is']
    _allow_pk = False
    _allow_autoincrement = False

    def __init__(self, tab_name, col_name, foreign_key: ForeignKey=None, primary_key=False, nullable=True):
        self.tab_name = tab_name
        self.col_name = col_name
        self.foreign_key = foreign_key
        self.primary_key = primary_key
        self.nullable = nullable
        self.order_direction = ''
        if self.autoincrement() and not self._allow_autoincrement:
            raise ColumnTypeError('It is forbidden to set the column nullable.')

    def __repr__(self):
        return '{} {} {}'.format(self.col_name, self.prototype(), '' if self.nullable else 'not null').strip()

    def __setattr__(self, key, value):
        super(NullType, self).__setattr__(key, value)
        if isinstance(value, ForeignKey):
            setattr(value, 'self_type', self)

    def __neg__(self):
        setattr(self, 'order_direction', 'DESC')
        return self

    def autoincrement(self):
        return self.primary_key and self.nullable

    def cast_value(self, value='null'):
        return value

    @classmethod
    def prototype(cls):
        return cls._prototype

    @classmethod
    def check_comparison_operator(cls, cmp_operator):
        if cmp_operator not in cls._supported_operators:
            raise ValueError('({}) - the unsupported comparison operator for type - {}.'.format(cmp_operator, cls.__name__))
        return True


class IntType(NullType):
    _prototype = 'INTEGER'
    _supported_operators = ['=', '>', '<', '!=', '>=', '<=']
    _allow_pk = True
    _allow_autoincrement = True

    def cast_value(self, value='null'):
        if self.nullable and value == 'null':
            return value
        return int(value)


class FloatType(NullType):
    _prototype = 'REAL'
    _supported_operators = ['=', '>', '<', '!=', '>=', '<=']

    def cast_value(self, value='null'):
        if self.nullable and value == 'null':
            return value
        return float(value)


class StrType(NullType):
    _prototype = 'VARCHAR(255)'
    _supported_operators = ['=', '!=', 'like']

    def cast_value(self, value='null'):
        if self.nullable and value == 'null':
            return value
        return str(value)


class BytesType(NullType):
    _prototype = 'BLOB'
    _supported_operators = ['=', '!=']

    def cast_value(self, value='null'):
        if self.nullable and value == 'null':
            return value
        return bytes(value)
