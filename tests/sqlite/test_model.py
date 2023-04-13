import unittest
import pytest

from orm import SQLiteDatabase, Model, Field, ForeignKey


class Author(Model):
    id = Field(int, primary_key=True, field_name='id')
    name = Field(str)
    age = Field(int)


class Book(Model):
    title = Field(str)
    author = ForeignKey(Author)


class TestModel(unittest.TestCase):
    def setUp(self):
        self.db = SQLiteDatabase('sqlite://:memory:')
        self.db.create_tables([Author, Book])

    def test_correct_table_name_conversion(self):
        # this is mainly to test that camelcase
        # is correctly converted to snake case
        class BookHTTPAuthor(Model):
            name = Field(str)
            year_born = Field(int)

        assert self.db._get_create_table_statement(
            BookHTTPAuthor,
        ) == (
            'CREATE TABLE book_http_author ('
            'pk INTEGER PRIMARY KEY AUTOINCREMENT, '
            'year_born INTEGER, name TEXT);'
        )

    def test_model_create_table_with_foreign_key(self):
        assert self.db._get_create_table_statement(
            Author,
        ) == (
            'CREATE TABLE author ('
            'name TEXT, id INTEGER PRIMARY KEY '
            'AUTOINCREMENT, age INTEGER);'
        )

        assert self.db._get_create_table_statement(
            Book,
        ) == (
            'CREATE TABLE book (pk INTEGER PRIMARY KEY AUTOINCREMENT, '
            'title TEXT, author_pk INTEGER, FOREIGN KEY(author_pk) '
            'REFERENCES author(id));'
        )

    def test_save_new_instance(self):
        author = Author(name='J. R. R. Tolkien', age=56)
        author.save(db=self.db)
        self.assertIsNotNone(author.pk)
        self.assertEqual(author.name, 'J. R. R. Tolkien')
        self.assertEqual(author.age, 56)

        book = Book(title='Quenta Silmarillion', author_pk=author.pk)
        book.save(db=self.db)
        self.assertIsNotNone(book.pk)
        self.assertEqual(book.pk, 1)
        self.assertEqual(book.title, 'Quenta Silmarillion')
        self.assertEqual(book.author.pk, author.pk)
        self.assertEqual(book.author, author)

    def test_update_existing_instance(self):
        author = Author(name='J. R. R. Tolkien', age=56)
        author.save(db=self.db)

        author.age = 57  # type:ignore # TODO please type checkers
        author.save(db=self.db)

        author_from_db = Author.get(pk=author.pk, db=self.db)
        self.assertEqual(author_from_db.age, 57)

    def test_delete_existing_instance(self):
        author = Author(name='J. R. R. Tolkien', age=56)
        author.save(db=self.db)

        author.delete()
        with pytest.raises(Author.DoesNotExist):
            _ = Author.get(pk=author.pk, db=self.db)

    def test_get_by_pk(self):
        author = Author(name='J. R. R. Tolkien', age=56)
        author.save(db=self.db)

        book = Book(title='Quenta Silmarillion', author_pk=author.pk)
        book.save(db=self.db)

        book_from_db = Book.get(pk=book.pk, db=self.db)
        self.assertEqual(book_from_db.title, 'Quenta Silmarillion')
        self.assertEqual(book_from_db.author.pk, author.pk)
        self.assertEqual(book_from_db.author, author)

    def test_foreign_key(self):
        author = Author(name='J. R. R. Tolkien', age=56)
        author.save(db=self.db)

        book = Book(title='Quenta Silmarillion', author_pk=author.pk)
        book.save(db=self.db)

        book_from_db = Book.get(pk=book.pk, db=self.db)
        self.assertEqual(book_from_db.author, author)
