from app.core.security import hash_password, verify_password


def test_password_hash_round_trip() -> None:
    hashed_password = hash_password("tharun1234")

    assert hashed_password.startswith("$2")
    assert verify_password("tharun1234", hashed_password)
    assert not verify_password("wrong-password", hashed_password)
