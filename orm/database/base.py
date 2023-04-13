import datetime
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from orm.field import Field, ForeignKey


if TYPE_CHECKING:
    from orm.model import Model

T = TypeVar('T', bound='Model')


SQL_TEMPLATES = {
    'create_table': {
        'sqlite': 'CREATE TABLE {table_name} ({fields}{constraints});',
    },
    'select': {
        'sqlite': 'SELECT * FROM {table_name} WHERE {placeholders};',
    },
    'insert': {
        'sqlite': (
            'INSERT INTO {table_name} '
            '({fields}) VALUES ({placeholders});'
        ),
    },
    'update': {
        'sqlite': 'UPDATE {table_name} SET {fields} WHERE {pk_fieldname} = ?;',
    },
    'delete': {
        'sqlite': 'DELETE FROM {table_name} WHERE {placeholders};',
    },
}
PYTHON_TYPE_TO_SQL_TYPE = {
    'sqlite': {
        int: 'INTEGER',
        float: 'REAL',
        str: 'TEXT',
        bytes: 'BLOB',
        bool: 'BOOLEAN',
        datetime.datetime: 'DATETIME',
        datetime.date: 'DATE',
        datetime.time: 'TIME',
    },
    'mysql': {
        int: 'INT',
        float: 'FLOAT',
        str: 'VARCHAR(255)',
        bytes: 'BLOB',
        bool: 'BOOLEAN',
        datetime.datetime: 'DATETIME',
        datetime.date: 'DATE',
        datetime.time: 'TIME',
    },
    'postgres': {
        int: 'INTEGER',
        float: 'NUMERIC',
        str: 'TEXT',
        bytes: 'BYTEA',
        bool: 'BOOLEAN',
        datetime.datetime: 'TIMESTAMP',
        datetime.date: 'DATE',
        datetime.time: 'TIME',
    }
}


class Database:
    db_url: str
    url_prefix: str

    class TooManyResultsReturned(Exception):
        pass

    class ModelInstanceHasNoPK(Exception):
        pass

    class UnexpectedResultType(Exception):
        pass

    def __init__(self, db_url: str) -> None:
        if not db_url.startswith(self.url_prefix):
            raise ValueError(
                f'Incorrect prefix in {db_url=} '
                f'(should be "{self.url_prefix}")'
            )
        self.db_url = db_url

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, Database)
            and __value.db_url == self.db_url
        )

    def _execute_sql(
        self,
        sql_statement: str,
        values: Optional[List[Any]] = None,
    ):
        raise NotImplementedError

    def get_sql_type(self, python_type: Type) -> str:
        return PYTHON_TYPE_TO_SQL_TYPE[self.url_prefix][python_type]

    def _get_create_table_statement(self, model: Type['Model']) -> str:
        fields: List[Tuple[str, str]] = []
        constraints = []
        primary_key_found = False
        for name, field in inspect.getmembers(model):
            if isinstance(field, ForeignKey):
                fields.append((f'{name}_pk', 'INTEGER'))
                constraints.append(
                    f'FOREIGN KEY({name}_pk) REFERENCES '
                    f'{name}({field.pk_field_name})',
                )
            elif isinstance(field, Field):
                if field.primary_key:
                    fields.insert(
                        0,
                        (
                            name,
                            self.get_sql_type(field.python_type)
                            + ' PRIMARY KEY AUTOINCREMENT'
                        )
                    )
                    primary_key_found = True
                else:
                    fields.insert(
                        0,
                        (name, self.get_sql_type(field.python_type)),
                    )
        if not primary_key_found:
            fields.insert(
                0,
                (
                    'pk',
                    self.get_sql_type(int) + ' PRIMARY KEY AUTOINCREMENT'
                ),
            )

        return SQL_TEMPLATES['create_table'][self.url_prefix].format(
            table_name=model.table_name(),
            fields=', '.join(' '.join(field) for field in fields),
            constraints=(', ' + ', '.join(constraints)) if constraints else '',
        )

    def _get_select_one_row_statement(
        self,
        model_cls: Type['Model'],
        pk: Any = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError

    def _get_update_existing_row_statement(
        self,
        instance: 'Model',
    ) -> Tuple[str, List]:
        raise NotImplementedError

    def _get_insert_new_row_statement(
        self,
        instance: 'Model',
    ) -> Tuple[str, List]:
        raise NotImplementedError

    def _get_delete_existing_row_statement(
        self,
        model: 'Model',
    ) -> str:
        raise NotImplementedError

    def create_table(self, model: Type['Model']):
        self._execute_sql(self._get_create_table_statement(model))

    def create_tables(self, models: List[Type['Model']]):
        for model in models:
            self.create_table(model)

    def get(self, model_cls: Type[T], pk: Any = None, **kwargs) -> T:
        if pk is not None:
            query = self._get_select_one_row_statement(
                pk=pk,
                model_cls=model_cls,
                **kwargs,
            )
        else:
            query = self._get_select_one_row_statement(
                model_cls=model_cls,
                **kwargs,
            )
        result = self._execute_sql(query)
        if not isinstance(result, list):
            raise self.UnexpectedResultType()
        if len(result) > 1:
            raise self.TooManyResultsReturned()
        elif len(result) < 1:
            raise model_cls.DoesNotExist
        return model_cls(**dict(result[0]))

    def save(self, instance: 'Model') -> 'Model':
        if instance.pk_field.field_name not in instance._data:
            query, values = self._get_insert_new_row_statement(instance)
            if instance.pk_field.field_name is None:
                raise ValueError('field_name not defined on pk field')
            pk_value = self._execute_sql(query, values)
            instance._data[instance.pk_field.field_name] = pk_value
        else:
            query, values = self._get_update_existing_row_statement(instance)
            self._execute_sql(query, values)
        return instance

    def delete(self, instance: 'Model') -> List:
        if not instance.pk:
            raise self.ModelInstanceHasNoPK()
        query = self._get_delete_existing_row_statement(instance)
        return self._execute_sql(query)
