"""AssemblyAI transcription for uploaded audio (preview after recording or saved recordings)."""

from __future__ import annotations

import logging
import os
import tempfile

from django.conf import settings

logger = logging.getLogger(__name__)


def transcribe_uploaded_file(uploaded_file) -> tuple[bool, str | None, str | None]:
    """
    Transcribe a Django UploadedFile via AssemblyAI.

    Returns:
        (success, text, error)
        If transcription is disabled (no API key): (False, None, None).
        On API/runtime failure: (False, None, error_message).
        On success: (True, text, None).
    """
    api_key = (getattr(settings, "ASSEMBLYAI_API_KEY", "") or "").strip()
    if not api_key:
        return False, None, None

    try:
        import assemblyai as aai
    except ImportError:
        logger.warning("assemblyai package not installed; skipping transcription.")
        return False, None, "Transcription is not available (missing dependency)."

    aai.settings.api_key = api_key
    base_url = (getattr(settings, "ASSEMBLYAI_BASE_URL", "") or "").strip()
    if base_url:
        aai.settings.base_url = base_url.rstrip("/")

    suffix = os.path.splitext(getattr(uploaded_file, "name", "") or "")[1] or ".webm"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        with open(tmp_path, "wb") as out:
            for chunk in uploaded_file.chunks():
                out.write(chunk)
        config = aai.TranscriptionConfig(
            speech_models=["universal-3-pro", "universal-2"],
            language_detection=True,
        )
        trans = aai.Transcriber().transcribe(tmp_path, config=config)
        ts = getattr(aai, "TranscriptStatus", None)
        if ts is not None and getattr(trans, "status", None) == ts.error:
            err_msg = getattr(trans, "error", None) or "Unknown transcription error"
            return False, None, str(err_msg)
        if getattr(trans, "error", None):
            return False, None, str(trans.error)
        text = (getattr(trans, "text", None) or "").strip()
        return True, text or None, None
    except Exception as exc:
        logger.exception("AssemblyAI transcription failed.")
        return False, None, str(exc)
    finally:
        if os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
