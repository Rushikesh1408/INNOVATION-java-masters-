from app.services.log_service import LogService


def test_sanitize_context_redacts_sensitive_values():
    raw = "email=user@example.com phone=555-123-4567 ssn=123-45-6789"
    cleaned = LogService._sanitize_context(raw)

    assert cleaned is not None
    assert "user@example.com" not in cleaned
    assert "555-123-4567" not in cleaned
    assert "123-45-6789" not in cleaned
    assert "[redacted-email]" in cleaned
    assert "[redacted-phone]" in cleaned
    assert "[redacted-ssn]" in cleaned


def test_pseudonymize_user_id_is_stable():
    first = LogService._pseudonymize_user_id(42)
    second = LogService._pseudonymize_user_id(42)

    assert first == second
    assert first is not None
    assert len(first) == 16


def test_pseudonymize_user_id_none():
    assert LogService._pseudonymize_user_id(None) is None
