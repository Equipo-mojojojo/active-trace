from __future__ import annotations

from app.core.security import decrypt_text, encrypt_text


def test_encryption_round_trip_and_no_plaintext_in_logs(caplog):
    plaintext = "sensitive-dni"

    encrypted = encrypt_text(plaintext)
    decrypted = decrypt_text(encrypted)

    assert encrypted != plaintext
    assert decrypted == plaintext
    assert plaintext not in caplog.text
