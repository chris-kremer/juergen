from security import get_configured_password_hash, hash_password, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("correct horse battery staple", iterations=1_000)

    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_invalid_hash_does_not_verify():
    assert not verify_password("password", "not-a-valid-hash")
    assert not verify_password("password", "pbkdf2_sha256$bad$salt$digest")


def test_load_password_hash_from_mapping():
    configured_hash = "pbkdf2_sha256$1000$salt$digest"

    assert get_configured_password_hash(
        "Annika",
        {"password_hashes": {"annika": configured_hash}},
    ) == configured_hash


def test_load_password_hash_from_environment(monkeypatch):
    configured_hash = "pbkdf2_sha256$1000$salt$digest"
    monkeypatch.setenv("PORTFOLIO_PASSWORD_HASH_ANNIKA", configured_hash)

    assert get_configured_password_hash("annika", {}) == configured_hash
