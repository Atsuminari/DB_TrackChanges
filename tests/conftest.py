import pytest
from sqlalchemy import create_engine

@pytest.fixture(scope="session")
def mariadb_engine():
    engine = create_engine("mysql+pymysql://myuser:mypassword@localhost:3306/mydatabase")
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def clean_database(mariadb_engine):
    with mariadb_engine.begin() as conn:
        conn.execute("DROP TABLE IF EXISTS test_table")
    yield
