from typing import Type


class Field:
    python_type: Type

    def __init__(self, python_type: Type) -> None:
        self.python_type = python_type


class ForeignKey(Field):
    def __init__(self, python_type: Type) -> None:
        super().__init__(python_type)
        self.id = Field(int)  # TODO: steal all fields from model


class ManyToMany(Field):
    pass
