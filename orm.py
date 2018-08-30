# coding: utf-8

from collections import OrderedDict
from sorm.utils import flat, dict_to_tuple
from sorm.objects import Base
from sorm.types import NullType
from sorm.errors import QueryError


class Query:
    def __init__(self, connection, table_obj: Base):
        Base.check_subclass(table_obj)
        self._connection = connection
        self._source_obj = table_obj
        self._source_tab = table_obj.table_name()
        self._tab_structure = OrderedDict({table_obj.table_name(): (table_obj, table_obj.get_column_names())})
        self._tab_results = []
        self._filters = []
        self._joined_tabs = {}
        self._ordering = []
        self._update_values = tuple()
        self._objects_dict = {}

    @classmethod
    def _get_table_creation_query_text(cls, table_obj: Base) -> str:
        columns = [repr(column) for column in table_obj.get_columns()]
        columns.append('PRIMARY KEY({})'.format(', '.join(table_obj.get_primary_keys())))
        columns.extend([repr(f_key) for f_key in table_obj.get_foreign_keys().values()])
        return 'CREATE TABLE IF NOT EXISTS {} ({})'.format(table_obj.table_name(), ', '.join(map(str, columns))).strip()

    @classmethod
    def _get_insert_query_text(cls, table_inst: Base) -> tuple:
        columns = table_inst.get_column_names()
        parameters = table_inst.get_column_values(columns)
        return 'INSERT INTO {} ({}) VALUES ({})'.format(table_inst.table_name(),
                                                        ', '.join(map(str, columns)),
                                                        ', '.join(['?' for _ in columns])), parameters

    def _get_select_query_text(self):
        sect_fields = ',\n'.join(flat([self._to_field_list(value[0], value[1]) for value in self._tab_structure.values()]))
        sect_from = '\n'.join(flat([[self._cast_table(self._source_obj)], self._joined_tabs.values()]))
        sect_where = 'WHERE {}'.format('\nAND '.join([e for e, _ in self._filters])) if len(self._filters) else ''
        sect_order = 'ORDER BY {}'.format(',\n'.join(self._ordering)) if len(self._ordering) else ''
        parameters = tuple(p for _, p in self._filters)  # tuple(flat([p for _, p in self._filters]))
        return 'SELECT\n{}\nFROM {}\n{}\n{}'.format(sect_fields, sect_from, sect_where, sect_order).strip(), parameters

    def _get_update_query_text(self):
        sect_what = self._cast_table(self._source_obj)
        sect_fields = self._update_values[0]
        sect_where = 'WHERE {}'.format('\nAND '.join([e for e, _ in self._filters])) if len(self._filters) else ''
        parameters = tuple(flat([self._update_values[1], [p for _, p in self._filters]]))
        return 'UPDATE {}\nSET {}\n{}'.format(sect_what, sect_fields, sect_where).strip(), parameters

    def _get_delete_query_text(self):
        sect_from = self._cast_table(self._source_obj)
        sect_where = 'WHERE {}'.format('\nAND '.join([e for e, _ in self._filters])) if len(self._filters) else ''
        parameters = tuple([p for _, p in self._filters])
        return 'DELETE FROM {}\n{}'.format(sect_from, sect_where).strip(), parameters

    def where(self, *filter_list):
        self._filters.extend([('\n{} {} ?'.format(self._cast_column(column),
                                                  cmp_oper if column.check_comparison_operator(cmp_oper) else None),
                              column.cast_value(value)) for column, cmp_oper, value in filter_list])
        return self

    def _cast_table(self, table_obj: Base) -> str:
        return table_obj.table_name()

    def _cast_column(self, column: NullType):
        if not self._tab_structure.get(column.tab_name):
            raise QueryError('({}) - the table is missing from query sources.'.format(column.tab_name))
        return column.col_name

    def _to_field_list(self, table_obj: Base, fields: list=None):
        if not fields:
            fields = table_obj.get_column_names()
        return [self._cast_column(column) for column in table_obj.get_columns_by_names(fields)]

    def _fetch(self, limit: int=None):
        text, params = self._get_select_query_text()
        self._parse_query_result(self._connection.execute('{}\nLIMIT {}'.format(text, limit) if limit else text, params))
        return self._get_result_as_object()

    def _update(self):
        text, params = self._get_update_query_text()
        self._connection.execute(text, params)

    def _delete(self):
        text, params = self._get_delete_query_text()
        self._connection.execute(text, params)

    def _parse_query_result(self, results: tuple) -> None:
        self._tab_results = []
        for result in results:
            res_iter = iter(result)
            self._tab_results.append(dict([(tab_name, dict([(key, next(res_iter)) for key in tab_fields[1]]))
                                           for tab_name, tab_fields in self._tab_structure.items()]))

    def _get_result_as_object(self) -> tuple:
        return tuple([self._handle_object_relations(
            self._get_object_from_dict(self._source_tab, self._objects_dict, tab_row.pop(self._source_tab)),
            tab_row, self._objects_dict) for tab_row in self._tab_results if len(tab_row)])

    def _handle_object_relations(self, source_obj, tab_row, objects_dict):
        if len(tab_row):
            relations = self._source_obj.get_relations()
            for key, value in relations.items():
                self._set_joint_object(source_obj, key, value, tab_row.pop(value), objects_dict)
            for key, value in tab_row.items():
                self._set_joint_object(source_obj, key, key, value, objects_dict)
        return source_obj

    def _set_joint_object(self, source_obj, attr_name, table_name, source_dict, objects_dict):
        setattr(source_obj, attr_name, self._get_object_from_dict(table_name, objects_dict, source_dict))

    def _get_object_from_dict(self, table_name, objects_dict, source_dict):
        class_obj = self._tab_structure.get(table_name)[0]
        if objects_dict.get(dict_to_tuple(source_dict)):
            source_obj = objects_dict.get(dict_to_tuple(source_dict))
        else:
            source_obj = class_obj(**source_dict)
            objects_dict.update({dict_to_tuple(source_dict): source_obj})
        return source_obj


class QuerySelect(Query):
    def __init__(self, connection, table_obj: Base, required_fields: list):
        super(QuerySelect, self).__init__(connection, table_obj)
        self._tab_structure = OrderedDict({table_obj.table_name():
                                           (table_obj,
                                            required_fields
                                            if len(required_fields)
                                            else table_obj.get_column_names())})
        self._joined_tabs = {}
        self._ordering = []
        for target_tab, foreign_key in table_obj.get_foreign_keys().items():
            self.join(foreign_key.bound_class, (foreign_key.self_type, '=',
                                                getattr(foreign_key.bound_class, foreign_key.bound_attr)))

    def join(self, table_obj: Base, *join_expr):
        self._tab_structure.update({table_obj.table_name():
                                   (table_obj, table_obj.get_column_names())})
        self._joined_tabs.update(self._get_formatted_join_list(table_obj, *join_expr
                                 if len(join_expr) else self._source_obj.get_foreign_relation(table_obj)))
        return self

    def order_by(self, *order_list):
        self._ordering.extend(['\n{} {}'.format(self._cast_column(column), column.order_direction).strip()
                              for column in order_list])
        return self

    def all(self):
        return self._fetch()

    def first(self, limit=1):
        return self._fetch(limit)

    def _cast_table(self, table_obj: Base) -> str:
        return '{} AS {}'.format(table_obj.table_name(), self._get_tab_synonym(table_obj.table_name()))

    def _cast_column(self, column: NullType):
        if not self._tab_structure.get(column.tab_name):
            raise QueryError('({}) - the table is missing from query sources.'.format(column.tab_name))
        return '{}.{}'.format(self._get_tab_synonym(column.tab_name), column.col_name)

    def _get_tab_synonym_index(self, tab_name) -> int:
        return tuple(self._tab_structure).index(tab_name) \
            if tab_name in self._tab_structure.keys() \
            else (len(self._tab_structure) + 1)

    def _get_tab_synonym(self, tab_name: str) -> str:
        return '{}_{}'.format(tab_name, self._get_tab_synonym_index(tab_name))

    def _get_formatted_join_list(self, table_obj: Base, *join_expr):
        if not len(join_expr):
            raise QueryError('A full join query is forbidden. Check the query.')
        return [(table_obj, 'LEFT JOIN {} on {}'.format(self._cast_table(table_obj),
                                                        ' and '.join(self._join_clause_list(*join_expr))))]

    def _join_clause_list(self, *join_expr):
        return ['{} {} {}'.format(self._cast_column(col_1), cmp_oper, self._cast_column(col_2))
                for col_1, cmp_oper, col_2 in join_expr
                if col_1.check_comparison_operator(cmp_oper) and col_1.check_comparison_operator(cmp_oper)]


class QueryUpdate(Query):
    def value(self, **kwargs):
        self._source_obj.check_names(kwargs.keys())
        tmp = list(zip(*[(k, v) for k, v in kwargs.items()]))
        self._update_values = (', '.join(['{}=?'.format(v) for v in tmp[0]]), tmp[1])
        self._update()
        return self._fetch()


class QueryDelete(Query):
    def where(self, *filter_list):
        super(QueryDelete, self).where(*filter_list)
        self._delete()

    @classmethod
    def delete(cls, connection, table_inst: Base):
        deletion = cls(connection, table_inst.__class__)
        deletion.where(*[(col, '=', getattr(table_inst, col.col_name))
                         for col in table_inst.get_columns()
                         if getattr(table_inst, col.col_name) != None])
        del table_inst
