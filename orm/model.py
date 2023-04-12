import inspect
import re
from typing import Any, Dict, TYPE_CHECKING, Optional, Type, TypeVar

from orm.field import Field, ForeignKey

if TYPE_CHECKING:
    from orm.database import Database

TABLE_NAME_PATTERNS = [
    re.compile(r'(.)([A-Z][a-z]+)'),
    re.compile(r'([a-z0-9])([A-Z])'),
]

T = TypeVar('T', bound='Model')


class Model:
    id: int
    _data: Dict

    class DoesNotExist(Exception):
        pass

    @classmethod
    def table_name(cls) -> str:
        table_name = cls.__name__
        for pattern in TABLE_NAME_PATTERNS:
            table_name = pattern.sub(r'\1_\2', table_name)
        return table_name.lower()

    def __init__(self, **kwargs):
        self._data = {
            'id': None
        }
        fields = [
            member[0]
            for member in inspect.getmembers(self.__class__)
            if isinstance(member[1], Field)
        ]
        for key, value in kwargs.items():
            if key in fields or key == 'id':
                self._data[key] = value
            elif key.removesuffix('_id') in fields:
                self._data[key] = value
            else:
                raise ValueError(f'field "{key}" not found in {fields=}')

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, self.__class__)
            and __value._data == self._data
        )

    def __getattribute__(self, __name: str) -> Any:
        _data = object.__getattribute__(self, '_data')
        if __name in _data or f'{__name}_id' in _data:
            if __name != 'id':
                field = object.__getattribute__(self, __name)
                if isinstance(field, ForeignKey):
                    if not self.__db:
                        raise ValueError(
                            'No knowledge of database detected for this'
                            'instance. Try saving it first'
                        )
                    return field.python_type.get(
                        id=_data[f'{__name}_id'],
                        db=self.__db,
                    )
            return _data[__name]
        return object.__getattribute__(self, __name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == '_data':
            object.__setattr__(self, __name, __value)
        elif __name in object.__getattribute__(self, '_data'):
            self._data[__name] = __value
        else:
            object.__setattr__(self, __name, __value)

    @classmethod
    def get(cls: Type[T], id: int, db: 'Database') -> T:
        try:
            instance = db.get(id=id, model_cls=cls)
        except db.UnexpectedResultType as exc:
            raise cls.DoesNotExist() from exc
        instance.__db = db
        return instance

    def save(self, db: 'Database') -> 'Model':
        self.__db = db
        saved = db.save(self)
        self.id = saved.id
        return saved

    def delete(self, db: Optional['Database'] = None):
        db = db or self.__db
        if not db:
            raise ValueError('Could not detect database.')
        return db.delete(self)
