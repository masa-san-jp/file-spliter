from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from src.config.constants import READ_BUFFER_SIZE

if TYPE_CHECKING:
    from src.services.cancellation import CancellationToken


def compute_sha256(path: Path, cancel_token: "CancellationToken | None" = None) -> str:
    """
    Compute the SHA-256 hash of a file using streaming reads.

    Args:
        path: Path to the file to hash.
        cancel_token: Optional cancellation token; raises CancelledError if set.

    Returns:
        Lowercase hex digest string.
    """
    digest = hashlib.sha256()

    with path.open("rb") as fh:
        while True:
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()

            chunk = fh.read(READ_BUFFER_SIZE)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()
