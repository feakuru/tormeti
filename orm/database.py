import datetime
import inspect
import sqlite3
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from orm.field import Field, ForeignKey


if TYPE_CHECKING:
    from orm.model import Model

T = TypeVar('T', bound='Model')


SQL_TEMPLATES = {
    'create_table': {
        'sqlite': 'CREATE TABLE {table_name} ({fields}{constraints});',
    },
    'insert': {
        'sqlite': (
            'INSERT INTO {table_name} '
            '({fields}) VALUES ({placeholders});'
        ),
    },
    'update': {
        'sqlite': 'UPDATE {table_name} SET {fields} WHERE id = ?;',
    }
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

    def __init__(self, db_url: str) -> None:
        if not db_url.startswith(self.url_prefix):
            raise ValueError(
                f'Incorrect prefix in {db_url=} '
                f'(should be "{self.url_prefix}")'
            )
        self.db_url = db_url

    def _execute_sql(
        self,
        sql_statement: str,
        values: Optional[List[Any]] = None,
    ):
        raise NotImplementedError

    def get_sql_type(self, python_type: Type) -> str:
        return PYTHON_TYPE_TO_SQL_TYPE[self.url_prefix][python_type]

    def _get_create_table_statement(self, model: Type['Model']) -> str:
        fields: List[Tuple[str, str]] = [
            ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        ]
        constraints = []
        for name, field in inspect.getmembers(model):
            if isinstance(field, ForeignKey):
                fields.append((f'{name}_id', 'INTEGER'))
                constraints.append(
                    f'FOREIGN KEY({name}_id) REFERENCES {name}(id)',
                )
            elif isinstance(field, Field):
                fields.append((name, self.get_sql_type(field.python_type)))

        return SQL_TEMPLATES['create_table'][self.url_prefix].format(
            table_name=model.table_name(),
            fields=', '.join(' '.join(field) for field in fields),
            constraints=(', ' + ', '.join(constraints)) if constraints else '',
        )

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

    def create_table(self, model: Type['Model']):
        print(f'boutta execute that {self._get_create_table_statement(model)}')
        self._execute_sql(self._get_create_table_statement(model))

    def create_tables(self, models: List[Type['Model']]):
        for model in models:
            self.create_table(model)

    def get(self, id: int, model_cls: Type[T]) -> T:
        raise NotImplementedError

    def save(self, instance: 'Model') -> 'Model':
        if not instance.id:
            query, values = self._get_insert_new_row_statement(instance)
            instance.id = self._execute_sql(query, values)
        else:
            query, values = self._get_update_existing_row_statement(instance)
            self._execute_sql(query, values)
        return instance


class SQLiteDatabase(Database):
    url_prefix = 'sqlite'

    def __init__(self, db_url: str) -> None:
        super().__init__(db_url)
        self.filename = db_url.removeprefix(f'{self.url_prefix}://')
        self.conn = sqlite3.connect(self.filename)

    def _execute_sql(
        self,
        sql_statement: str,
        values: Optional[List[Any]] = None,
    ) -> Union[int, List[Tuple[Any]]]:
        cursor = self.conn.cursor()
        if values:
            result = cursor.execute(sql_statement, values)
        else:
            result = cursor.execute(sql_statement)
        return result.fetchall() or cursor.lastrowid or cursor.rowcount

    def _get_update_existing_row_statement(
        self,
        instance: 'Model',
    ) -> Tuple[str, List]:
        fields = ','.join([f"{k} = ?" for k in instance._data.keys()])
        values = list(instance._data.values())
        values.append(instance.id)
        query = SQL_TEMPLATES['update']['sqlite'].format(
            table_name=instance.table_name(),
            fields=fields,
        )
        return query, values

    def _get_insert_new_row_statement(
        self,
        instance: 'Model',
    ) -> Tuple[str, List]:
        fields = ','.join(instance._data.keys())
        placeholders = ','.join(['?'] * len(instance._data))
        values = list(instance._data.values())
        query = SQL_TEMPLATES['insert']['sqlite'].format(
            table_name=instance.table_name(),
            fields=fields,
            placeholders=placeholders,
        )
        return query, values
