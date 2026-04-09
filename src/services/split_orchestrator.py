from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from src.config.settings import SplitSettings
from src.core.file_detector import detect_kind
from src.core.job import SplitJob, SplitResult
from src.services.cancellation import CancellationToken
from src.splitters import splitter_factory
from src.utils.errors import CancelledError, FFmpegNotFoundError, FileSplitterError
from src.utils.paths import ensure_dir, is_hidden_or_temp

logger = logging.getLogger("file_splitter.orchestrator")

ProgressCallback = Callable[[str, float], None]   # (current_file, 0.0–1.0)
ResultCallback = Callable[[SplitResult], None]
FileCountCallback = Callable[[int], None]


def run(
    settings: SplitSettings,
    on_file_count: FileCountCallback | None = None,
    on_progress: ProgressCallback | None = None,
    on_result: ResultCallback | None = None,
    cancel_token: CancellationToken | None = None,
) -> list[SplitResult]:
    """
    Scan the input directory, classify files, and run the appropriate splitter.

    Raises FileSplitterError if the input directory does not exist.
    Returns a list of SplitResult for each candidate file processed.
    """
    if not settings.input_path.is_dir():
        raise FileSplitterError(
            f"Input folder does not exist: {settings.input_path}"
        )

    ensure_dir(settings.output_path)

    candidates = _collect_candidates(settings.input_path)

    if on_file_count:
        on_file_count(len(candidates))

    if not candidates:
        logger.info("No files found in %s", settings.input_path)
        return []

    results: list[SplitResult] = []

    for idx, source_path in enumerate(candidates):
        if cancel_token and cancel_token.is_cancelled:
            logger.info("Processing cancelled after %d/%d files.", idx, len(candidates))
            break

        result = _process_file(source_path, settings, on_progress, cancel_token)
        results.append(result)

        if on_result:
            on_result(result)

        _log_result(result)

    return results


def _collect_candidates(input_path: Path) -> list[Path]:
    return sorted(
        f for f in input_path.iterdir()
        if f.is_file() and not is_hidden_or_temp(f)
    )


def _process_file(
    source_path: Path,
    settings: SplitSettings,
    on_progress: ProgressCallback | None,
    cancel_token: CancellationToken | None,
) -> SplitResult:
    logger.info("Processing: %s", source_path.name)

    kind = detect_kind(source_path)
    logger.info("Kind detected: %s -> %s", source_path.name, kind)

    job = SplitJob(source_path=source_path, kind=kind, settings=settings)
    splitter = splitter_factory.create(kind)

    def file_progress(ratio: float) -> None:
        if on_progress:
            on_progress(source_path.name, ratio)

    try:
        out_dir, metadata = splitter.split(job, file_progress, cancel_token)
        return SplitResult.ok(job, out_dir, metadata)

    except CancelledError as exc:
        return SplitResult.fail(job, f"Cancelled: {exc}")

    except FFmpegNotFoundError as exc:
        logger.error("ffmpeg unavailable for %s: %s", source_path.name, exc)
        return SplitResult.fail(job, str(exc))

    except FileSplitterError as exc:
        logger.error("Splitter error for %s: %s", source_path.name, exc)
        return SplitResult.fail(job, str(exc))

    except PermissionError as exc:
        logger.error("Permission denied for %s: %s", source_path.name, exc)
        return SplitResult.fail(job, f"Permission denied: {exc}")

    except OSError as exc:
        logger.error("OS error for %s: %s", source_path.name, exc)
        return SplitResult.fail(job, f"OS error: {exc}")

    except Exception as exc:
        logger.exception("Unexpected error for %s", source_path.name)
        return SplitResult.fail(job, f"Unexpected error: {exc}")


def _log_result(result: SplitResult) -> None:
    name = result.job.source_path.name
    if result.success:
        assert result.metadata is not None
        logger.info(
            "Done: %s -> %d parts, output: %s",
            name,
            result.metadata.part_count,
            result.output_dir,
        )
    else:
        logger.error("Failed: %s -> %s", name, result.error_message)
