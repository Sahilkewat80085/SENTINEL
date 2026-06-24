from app.services.content_verification import ContentVerificationService


def test_normalize_and_hash() -> None:
    """Test content verification line-ending normalization and SHA256 hashing."""
    service = ContentVerificationService()

    content_lf = b"key: value\nport: 8080\n"
    content_crlf = b"key: value\r\nport: 8080\r\n"
    content_extra = b"key: value\nport: 8080\n\n\n"

    # Hashing should be identical regardless of CRLF vs LF and trailing newlines
    hash_lf = service.normalize_and_hash(content_lf)
    hash_crlf = service.normalize_and_hash(content_crlf)
    hash_extra = service.normalize_and_hash(content_extra)

    assert hash_lf == hash_crlf
    assert hash_lf == hash_extra

    # Matches hardcoded SHA256 of "key: value\nport: 8080"
    expected = "d7862ab5644b3e9dcb44b2f06ed0cade63e11282e81c5cf947367f30c324f0c6"
    assert hash_lf == expected
