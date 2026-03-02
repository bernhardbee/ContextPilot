"""Tests for security audit persistence utilities."""
import os
import tempfile
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import database
import security_audit


@pytest.fixture(scope="function")
def audit_db(monkeypatch):
    """Create isolated sqlite database for audit persistence tests."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()

    test_engine = create_engine(f"sqlite:///{temp_file.name}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    @contextmanager
    def test_db_session():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", SessionLocal)
    monkeypatch.setattr(database, "get_db_session", test_db_session)
    monkeypatch.setattr(security_audit, "get_db_session", test_db_session)

    yield

    test_engine.dispose()
    os.unlink(temp_file.name)


class TestSecurityAuditPersistence:
    def test_persist_and_list_security_event(self, audit_db):
        security_audit.persist_security_event(
            event="api_key_auth",
            outcome="valid_key",
            actor="api_key:abcd***",
            details={"source": "test"},
        )

        events = security_audit.list_security_events(limit=10, offset=0)
        assert len(events) == 1
        assert events[0].event == "api_key_auth"
        assert events[0].outcome == "valid_key"
        assert events[0].actor == "api_key:abcd***"
        assert events[0].details.get("source") == "test"

    def test_list_security_events_filters(self, audit_db):
        security_audit.persist_security_event(event="api_key_auth", outcome="valid_key")
        security_audit.persist_security_event(event="request_signing", outcome="invalid_signature")

        filtered = security_audit.list_security_events(limit=10, offset=0, event="request_signing")
        assert len(filtered) == 1
        assert filtered[0].event == "request_signing"
        assert filtered[0].outcome == "invalid_signature"
