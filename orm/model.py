import re
from typing import Any, Dict, TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    from .database import Database

TABLE_NAME_PATTERNS = [
    re.compile(r'(.)([A-Z][a-z]+)'),
    re.compile(r'([a-z0-9])([A-Z])'),
]

T = TypeVar('T', bound='Model')


class Model:
    id: int
    _data: Dict

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
        for key, value in kwargs.items():
            self._data[key] = value

    def __getattribute__(self, __name: str) -> Any:
        _data = object.__getattribute__(self, '_data')
        if __name in _data:
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
        return db.get(id=id, model_cls=cls)

    def save(self, db: 'Database') -> 'Model':
        return db.save(self)
