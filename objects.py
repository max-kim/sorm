# coding: utf-8

from sorm.errors import ColumnIsNotFoundError, StructureError
from sorm.types import NullType, IntType


class Relationship:
    """Set a relation with object attribute and foreign key target table.
    Defined attribute will contain DB object instance consistent with foreign key.
    """
    def __init__(self, self_attr: NullType):
        if not self_attr.foreign_key:
            raise ValueError('The attribute ({}) does not contain a foreign key.'.format(self_attr.col_name))
        self.self_attr = self_attr
        self.bound_attr = getattr(self_attr.foreign_key.bound_class, self_attr.foreign_key.bound_attr)


class Base:
    """Superclass for all custom table objects.
    The all custom table objects must be extended from this one."""
    __tablename__ = ''

    id = IntType(__tablename__, 'id', primary_key=True)

    def __init__(self, **kwargs):
        self.check_names(kwargs.keys())
        for column in self.get_columns():
            if kwargs.get(column.col_name) == None and not (column.nullable and column.autoincrement):
                raise ValueError('The value of column ({}) must not be a None!'.format(column.col_name))
            setattr(self, column.col_name, kwargs.get(column.col_name))

    def __repr__(self):
        return '{\'%s\': {%s}}' % (self.__tablename__,
                                   ', '.join(['\'{}\': \'{}\''.format(k, v) for k, v in self.__dict__.items()
                                              if k in set(self.get_column_names())]))

    def get_column_values(self, column_names):
        return tuple([getattr(self, key) for key in column_names])

    @classmethod
    def table_name(cls) -> str:
        return cls.__tablename__

    @classmethod
    def create(cls, connection) -> None:
        connection.create_table(cls)

    @classmethod
    def get_field_names(cls) -> list:
        return [k for k in cls.__dict__.keys() if not k.startswith('__')]

    @classmethod
    def get_column_names(cls) -> list:
        return [k for k, v in cls.__dict__.items() if isinstance(v, NullType)]

    @classmethod
    def parse_column_names(cls, columns_str: str) -> list:
        column_names = [v.strip() for v in columns_str.split(',')]
        return cls.check_names(*column_names)

    @classmethod
    def get_columns_by_names(cls, columns: (list, str)) -> list:
        if isinstance(columns, str):
            columns = cls.parse_column_names(columns)
        return [cls.__dict__.get(col_name) for col_name in columns]

    @classmethod
    def get_columns(cls) -> list:
        return [v for v in cls.__dict__.values() if isinstance(v, NullType)]

    @classmethod
    def get_primary_keys(cls) -> list:
        primary_key_list = [col.col_name for col in cls.get_columns() if col.primary_key]
        if any(col.autoincrement() for col in cls.get_columns()) and len(primary_key_list) > 1:
            raise StructureError('SQLite does not support autoincrement with multiple primary key. Set primary key column not nullable.')
        return primary_key_list

    @classmethod
    def get_foreign_keys(cls) -> dict:
        return dict([(col, col.foreign_key) for col in cls.get_columns() if col.foreign_key])

    @classmethod
    def get_relations(cls) -> dict:
        return dict([(k, v.bound_attr.tab_name) for k, v in cls.__dict__.items() if isinstance(v, Relationship)])

    @classmethod
    def get_foreign_relation(cls, table_obj):
        return tuple((col, '=', getattr(col.foreign_key.bound_class, col.foreign_key.bound_attr)) for col in cls.get_columns() if col.foreign_key and col.foreign_key.bound_class == table_obj)

    @classmethod
    def check_structure(cls, *args) -> None:
        if len(args):
            cls.check_names(args)
        cls.check_types()
        if not len(cls.get_primary_keys()):
            StructureError('There is no primary key in the table.')

    @classmethod
    def check_names(cls, name_list: list) -> list:
        not_found_keys = [key for key in name_list if key not in cls.get_column_names()]
        not_found_len = len(not_found_keys)
        if not_found_len:
            raise ColumnIsNotFoundError('The column{} ({}) {} not found for table ({})!'.format(
                's' if not_found_len > 1 else '',
                ', '.join(not_found_keys),
                'are' if not_found_len > 1 else 'is',
                cls.table_name()
            ))
        return name_list

    @classmethod
    def check_types(cls) -> None:
        for key in cls.get_column_names():
            if getattr(cls, key).tab_name != cls.table_name():
                raise StructureError('({}) - the incorrect table name was defined in the column type.'.
                                     format(getattr(cls, key).col_name))
            if getattr(cls, key).col_name != key:
                raise StructureError('({}) - the incorrect column name was defined in the column type.'.
                                     format(getattr(cls, key).col_name))

    @classmethod
    def check_subclass(cls, checked_obj):
        if not issubclass(checked_obj, cls):
            raise ValueError('{} does not seem like subclass of Base!'.format(checked_obj.__name__))
