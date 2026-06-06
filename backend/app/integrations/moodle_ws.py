"""
MoodleWSClient: Client for Moodle Web Services REST API.

Design D4: Encapsulates all LMS communication.
- Credentials come from env vars MOODLE_URL and MOODLE_TOKEN.
- MoodleNotConfiguredError is raised when credentials are missing.
- MoodleWSError is raised on network errors or non-2xx responses.
- Timeout: MOODLE_TIMEOUT env var (default 30s).

Usage::

    client = MoodleWSClient()
    users = await client.get_enrolled_users(course_id="42")
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class MoodleNotConfiguredError(RuntimeError):
    """Raised when MOODLE_URL or MOODLE_TOKEN are not configured."""


class MoodleWSError(RuntimeError):
    """Raised when the Moodle WS call fails (network error or non-2xx response)."""


def _get_credentials() -> tuple[str, str]:
    """Return (MOODLE_URL, MOODLE_TOKEN) from environment.

    Raises MoodleNotConfiguredError if either is missing or empty.
    """
    url = os.environ.get("MOODLE_URL", "").strip()
    token = os.environ.get("MOODLE_TOKEN", "").strip()

    if not url or not token:
        raise MoodleNotConfiguredError(
            "Las variables de entorno MOODLE_URL y MOODLE_TOKEN son requeridas "
            "para la integración con Moodle. Configuralas o importá el padrón "
            "manualmente desde archivo."
        )

    return url, token


class MoodleWSClient:
    """Async client for Moodle Web Services.

    Methods raise MoodleNotConfiguredError or MoodleWSError — never raw
    httpx exceptions — so callers only deal with domain-level errors.
    """

    def __init__(self, timeout: float | None = None):
        env_timeout = float(os.environ.get("MOODLE_TIMEOUT", "30"))
        self._timeout = timeout if timeout is not None else env_timeout

    async def get_enrolled_users(self, course_id: str | int) -> list[dict[str, Any]]:
        """Return enrolled users for a Moodle course.

        Returns a list of dicts with keys: nombre, apellidos, email (and
        the raw Moodle fields for forward compatibility).

        Raises:
            MoodleNotConfiguredError: credentials not set.
            MoodleWSError: network error or non-2xx response.
        """
        base_url, token = _get_credentials()

        params = {
            "wstoken": token,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": str(course_id),
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{base_url}/webservice/rest/server.php", params=params)
        except httpx.TimeoutException as exc:
            raise MoodleWSError(
                f"Timeout al conectar con Moodle (>{self._timeout}s). "
                "Reintentá en unos minutos o importá el padrón manualmente."
            ) from exc
        except httpx.RequestError as exc:
            raise MoodleWSError(
                f"Error de red al conectar con Moodle: {exc}. "
                "Reintentá en unos minutos o importá el padrón manualmente."
            ) from exc

        if response.status_code >= 400:
            raise MoodleWSError(
                f"Moodle respondió con HTTP {response.status_code}. "
                "Reintentá en unos minutos o importá el padrón manualmente."
            )

        data = response.json()

        # Moodle returns {"exception": "..."} for function-level errors
        if isinstance(data, dict) and "exception" in data:
            raise MoodleWSError(
                f"Moodle WS error: {data.get('message', data.get('exception'))}. "
                "Reintentá en unos minutos o importá el padrón manualmente."
            )

        # Normalise to project field names
        return [_normalise_moodle_user(u) for u in data]

    async def get_course_activities(self, course_id: str | int) -> list[dict[str, Any]]:
        """Return activities/resources for a Moodle course.

        Raises:
            MoodleNotConfiguredError: credentials not set.
            MoodleWSError: network error or non-2xx response.
        """
        base_url, token = _get_credentials()

        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_contents",
            "moodlewsrestformat": "json",
            "courseid": str(course_id),
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{base_url}/webservice/rest/server.php", params=params)
        except httpx.TimeoutException as exc:
            raise MoodleWSError(
                f"Timeout al conectar con Moodle (>{self._timeout}s)."
            ) from exc
        except httpx.RequestError as exc:
            raise MoodleWSError(f"Error de red al conectar con Moodle: {exc}.") from exc

        if response.status_code >= 400:
            raise MoodleWSError(
                f"Moodle respondió con HTTP {response.status_code}."
            )

        data = response.json()

        if isinstance(data, dict) and "exception" in data:
            raise MoodleWSError(
                f"Moodle WS error: {data.get('message', data.get('exception'))}."
            )

        return data if isinstance(data, list) else []


def _normalise_moodle_user(raw: dict[str, Any]) -> dict[str, Any]:
    """Map Moodle user fields to project-canonical field names."""
    return {
        "nombre": raw.get("firstname", ""),
        "apellidos": raw.get("lastname", ""),
        "email": raw.get("email", ""),
        "moodle_id": raw.get("id"),
        "username": raw.get("username", ""),
        "_raw": raw,
    }
