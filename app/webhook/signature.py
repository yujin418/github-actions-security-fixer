"""GitHub webhook signature verification (HMAC-SHA256).

GitHub signs each delivery with the webhook secret and sends the digest in the
``X-Hub-Signature-256`` header as ``sha256=<hex>``. We recompute it over the
raw request body and compare in constant time.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    """Return True when the header matches the HMAC-SHA256 of ``body``."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
