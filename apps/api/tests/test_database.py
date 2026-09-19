from opspilot_api.database import normalize_database_url


def test_postgresql_url_uses_psycopg3_driver() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@db.example.test/app")
        == "postgresql+psycopg://user:pass@db.example.test/app"
    )


def test_sqlite_url_is_unchanged() -> None:
    assert normalize_database_url("sqlite:///./opspilot.db") == "sqlite:///./opspilot.db"
