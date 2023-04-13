import inspect
from typing import Optional, Type


class Field:
    python_type: Type
    primary_key: bool
    field_name: Optional[str]

    class NoFieldNameProvidedForPrimaryKey(Exception):
        pass

    def __init__(
        self,
        python_type: Type,
        primary_key: bool = False,
        field_name: Optional[str] = None,
    ) -> None:
        self.python_type = python_type
        self.primary_key = primary_key
        if primary_key:
            if not field_name:
                raise self.NoFieldNameProvidedForPrimaryKey()
            self.field_name = field_name


class ForeignKey(Field):
    pk_field_name: str = ''

    @property
    def pk(self):
        return getattr(self, self.pk_field_name)

    def __init__(self, python_type: Type) -> None:
        super().__init__(python_type)
        for fieldname, field in inspect.getmembers(python_type):
            if isinstance(field, Field):
                setattr(self, fieldname, field)
                if field.primary_key:
                    self.pk_field_name = fieldname
        if not self.pk_field_name:
            self.pk_field_name = 'pk'


class ManyToMany(Field):
    pass
