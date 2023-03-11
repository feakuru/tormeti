from typing import Type


class Field:
    python_type: Type

    def __init__(self, python_type: Type) -> None:
        self.python_type = python_type


class ForeignKey(Field):
    pass


class ManyToMany(Field):
    pass
