"""
Tests for SettingsStore persistence.
"""
from pathlib import Path
from sqlalchemy import create_engine, inspect

from database import Base
from settings_store import SettingsStore, SettingsModel


def test_settings_store_round_trip(tmp_path: Path):
    """SettingsStore can persist and retrieve values from a temp database."""
    db_path = tmp_path / "settings_test.db"
    db_url = f"sqlite:///{db_path}"

    # Create tables using shared Base
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)

    # Verify settings table exists
    inspector = inspect(engine)
    assert "settings" in inspector.get_table_names()

    store = SettingsStore(db_url)
    store.set("openai_api_key", "test-key")

    assert store.get("openai_api_key") == "test-key"
    assert store.get("missing", default="fallback") == "fallback"

    store.delete("openai_api_key")
    assert store.get("openai_api_key") is None
