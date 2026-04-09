from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from src.services.cancellation import CancellationToken
from src.utils.errors import CancelledError, FFmpegNotFoundError

logger = logging.getLogger("file_splitter.ffmpeg_runner")


def ensure_available() -> None:
    """Check that ffmpeg and ffprobe are available on PATH."""
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise FFmpegNotFoundError(
                f"'{tool}' not found on PATH. "
                "Install ffmpeg to enable audio/video splitting."
            )


def get_duration_seconds(path: Path) -> float:
    """Use ffprobe to retrieve the duration of a media file in seconds."""
    ensure_available()
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "--",
            str(path.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    raw = result.stdout.strip()
    if not raw or raw == "N/A":
        return 0.0
    return float(raw)


def get_stream_info(path: Path) -> dict[str, bool]:
    """Return dict with 'has_video' and 'has_audio' booleans."""
    ensure_available()
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "--",
            str(path.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    has_video = bool(result.stdout.strip())

    result_a = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "--",
            str(path.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    has_audio = bool(result_a.stdout.strip())
    return {"has_video": has_video, "has_audio": has_audio}


def run_ffmpeg(
    args: list[str],
    on_progress: Callable[[str], None] | None = None,
    cancel_token: CancellationToken | None = None,
    timeout: int = 3600,
) -> None:
    """
    Run an ffmpeg command.

    Args:
        args: Full argument list (excluding 'ffmpeg' itself).
        on_progress: Optional callback receiving stderr lines for progress parsing.
        cancel_token: Optional token to support cancellation.
        timeout: Maximum allowed seconds before forceful kill.

    Raises:
        CancelledError: If cancellation is requested.
        RuntimeError: If ffmpeg exits with a non-zero code.
    """
    cmd = ["ffmpeg", "-y"] + args
    logger.debug("Running: %s", " ".join(cmd))

    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
    )

    try:
        assert process.stderr is not None
        for line in process.stderr:
            if cancel_token and cancel_token.is_cancelled:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise CancelledError("ffmpeg process cancelled.")

            if on_progress:
                on_progress(line.rstrip())

        process.wait(timeout=timeout)

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError(f"ffmpeg timed out after {timeout}s.")

    except CancelledError:
        raise

    except Exception:
        process.kill()
        process.wait()
        raise

    finally:
        if process.stderr:
            process.stderr.close()

    if process.returncode not in (0, None):
        raise RuntimeError(f"ffmpeg exited with code {process.returncode}.")
