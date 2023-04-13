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
    _data: Dict

    class DoesNotExist(Exception):
        pass

    class TooManyPrimaryKeys(Exception):
        pass

    @property
    def pk_field(self) -> Field:
        return self._pk_field

    @classmethod
    def table_name(cls) -> str:
        table_name = cls.__name__
        for pattern in TABLE_NAME_PATTERNS:
            table_name = pattern.sub(r'\1_\2', table_name)
        return table_name.lower()

    def __init__(self, **kwargs):
        self._data = {}
        provided_fields = kwargs.items()
        all_fields = inspect.getmembers(self.__class__)
        primary_key = list(filter(
            lambda field: getattr(field[1], 'primary_key', False),
            all_fields
        ))
        if not primary_key:
            pk = Field(int, primary_key=True, field_name='pk')
            all_fields.append(('pk', pk))
            setattr(self, 'pk', pk)
            setattr(self, '_pk_field', pk)
        elif len(primary_key) > 1:
            raise self.TooManyPrimaryKeys()
        else:
            setattr(
                self,
                'pk',
                property(
                    lambda self: getattr(
                        self,
                        primary_key[0][1].field_name,
                    )
                )
            )
            setattr(self, '_pk_field', primary_key[0][1])
        fields = [
            member[0]
            for member in all_fields
            if (
                isinstance(member[1], Field)
                and not member[0].startswith('__')
            )
        ]
        for key, value in provided_fields:
            if key in fields:
                self._data[key] = value
            elif key.removesuffix('_pk') in fields:
                self._data[key] = value
            else:
                raise ValueError(f'field "{key}" not found in {fields=}')

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            lhs, rhs = self._data, __value._data
            pk_field_name = self.pk_field.field_name
            if (
                pk_field_name not in lhs
                or pk_field_name not in rhs
            ):
                if pk_field_name in lhs:
                    del lhs[pk_field_name]
                if pk_field_name in rhs:
                    del rhs[pk_field_name]
            return lhs == rhs
        return False

    def __getattribute__(self, __name: str) -> Any:
        _data = object.__getattribute__(self, '_data')
        if __name == '_pk_field':
            return object.__getattribute__(self, '_pk_field')
        if hasattr(self, '_pk_field'):
            pk_field = object.__getattribute__(self, '_pk_field')
            if __name in [pk_field.field_name, 'pk']:
                return self._data.get(pk_field.field_name, None)
        if __name in _data or f'{__name}_pk' in _data:
            field = object.__getattribute__(self, __name)
            if isinstance(field, ForeignKey):
                if not self.__db:
                    raise ValueError(
                        'No knowledge of database detected for this'
                        'instance. Try saving it first'
                    )
                get_kwargs = {field.pk_field_name: _data[f'{__name}_pk']}
                return field.python_type.get(
                    db=self.__db,
                    **get_kwargs,
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
    def get(cls: Type[T], db: 'Database', pk: Any = None, **kwargs) -> T:
        try:
            instance = db.get(pk=pk, model_cls=cls, **kwargs)
        except db.UnexpectedResultType as exc:
            raise cls.DoesNotExist() from exc
        instance.__db = db
        return instance

    def save(self, db: 'Database') -> 'Model':
        self.__db = db
        db.save(self)
        return self

    def delete(self, db: Optional['Database'] = None):
        db = db or self.__db
        if not db:
            raise ValueError('Could not detect database.')
        return db.delete(self)
