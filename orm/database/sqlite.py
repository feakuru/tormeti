import sqlite3
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from orm.database.base import (
    SQL_TEMPLATES,
    Database,
)


if TYPE_CHECKING:
    from orm.model import Model


class SQLiteDatabase(Database):
    url_prefix = 'sqlite'

    def __init__(self, db_url: str) -> None:
        super().__init__(db_url)
        self.filename = db_url.removeprefix(f'{self.url_prefix}://')
        self.conn = sqlite3.connect(self.filename)
        self.conn.row_factory = sqlite3.Row

    def _execute_sql(
        self,
        sql_statement: str,
        values: Optional[List[Any]] = None,
    ) -> Union[int, List[sqlite3.Row], None]:
        cursor = self.conn.cursor()
        if values:
            result = cursor.execute(sql_statement, values)
        else:
            result = cursor.execute(sql_statement)
        return result.fetchall() or cursor.lastrowid

    def _get_select_one_row_statement(
        self,
        id: int,
        model_cls: Type['Model'],
    ) -> str:
        query = SQL_TEMPLATES['select']['sqlite'].format(
            table_name=model_cls.table_name(),
            placeholders=f'id={id}',
        )
        return query

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

    def _get_delete_existing_row_statement(
        self,
        model: 'Model',
    ) -> str:
        query = SQL_TEMPLATES['delete']['sqlite'].format(
            table_name=model.__class__.table_name(),
            placeholders=f'id={model.id}',
        )
        return query
