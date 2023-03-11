# Tormeti

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

__Tormeti__ is an ORM library for Python. It's still in early development, but we plan to eventually support SQLite, MySQL, and PostgreSQL.

## Installation

TODO: add instructions for installation.

## Usage

To use Tormeti, you need to define your database models as subclasses of the Model class. Each model represents a table in the database, and each attribute of the model represents a column in the table. You can use the Field class to specify the type of each column.

Here's an example:

```python
from orm import Model, Field

class User(Model):
    username = Field(str)
    email = Field(str)
    age = Field(int)
```

This defines a User model with four columns: id (an integer primary key which is automatically defined on all models), username (a string), an email (a string) and an age (integer).

To interact with the database, you first need to create a database object using one of the supported database URLs:

```python
from orm import SQLiteDatabase

db = SQLiteDatabase('sqlite://:memory:')
```
This creates an SQLite database in memory.

You can then create the table corresponding to your model using the `create_table` method (or `create_tables` for multiple):

```python
db.create_table(User)
# or
db.create_tables([User, ...])
```

This generates and executes the SQL statement necessary to create the User table in the database.

You can then create new instances of your model and save them to the database:

```python
user = User(
    id=1,
    username='john',
    email='john@example.com',
)
user.save()
```

This creates a new row in the User table with the specified values.

You can retrieve instances from the database using the get method:

```python
user = User.get(id=1)
```

This retrieves the User instance with the specified id value.

You can also update and delete instances using the save and delete methods:

```python
user.username = 'jane'
user.save()

user.delete()
```

## Current database support

| Database   |    Supported   |
|------------|----------------|
| SQLite     | ✅ (partially) |
| MySQL      | ❌             |
| PostgreSQL | ❌             |

## Contributing

Contributions are welcome! If you find a bug or have an idea for a new feature, please open an issue on GitHub. If you would like to contribute code, please open a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.
