from orm import SQLiteDatabase


def test_create_database():
    db = SQLiteDatabase(db_url="sqlite://test.db")
    assert db.filename == 'test.db'
