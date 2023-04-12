from orm import create_database, SQLiteDatabase


def test_create_database():
    db = create_database(db_url='sqlite://test.db')
    assert isinstance(db, SQLiteDatabase)
    assert db.filename == 'test.db'
    assert db == SQLiteDatabase(db_url='sqlite://test.db')
