"""BMW CarData REST API client."""
from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .auth import TokenData, refresh_access_token
from .const import (
    API_BASE_URL,
    API_VERSION_HEADER,
    CONF_CLIENT_ID,
    CONTAINER_NAME,
    CONTAINER_PURPOSE,
    DESCRIPTORS,
    TOKEN_REFRESH_BUFFER_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


class BMWCarDataAPI:
    """Thin async wrapper around the BMW CarData REST API."""

    def __init__(self, session: aiohttp.ClientSession, client_id: str, token: TokenData) -> None:
        self._session = session
        self._client_id = client_id
        self._token = token

    # ── Token management ──────────────────────────────────────────────────────

    async def _ensure_token(self) -> None:
        """Refresh the access token if it is close to expiry."""
        if time.time() >= self._token.expires_at - TOKEN_REFRESH_BUFFER_SECONDS:
            _LOGGER.debug("Refreshing access token")
            self._token = await refresh_access_token(
                self._session, self._client_id, self._token.refresh_token
            )

    def get_current_token(self) -> TokenData:
        return self._token

    def _auth_headers(self) -> dict[str, str]:
        return {
            **API_VERSION_HEADER,
            "Authorization": f"Bearer {self._token.access_token}",
        }

    # ── Low-level request helpers ──────────────────────────────────────────────

    async def _get(self, path: str, **kwargs: Any) -> Any:
        await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        _LOGGER.debug("GET %s", url)
        async with self._session.get(url, headers=self._auth_headers(), **kwargs) as resp:
            if resp.status == 401:
                raise PermissionError("BMW API returned 401 – token may be revoked")
            if resp.status == 403:
                body = await resp.text()
                _LOGGER.error(
                    "BMW API returned 403 for %s – CarData API access may not be "
                    "enabled in the BMW portal. Response: %s", url, body
                )
                raise PermissionError(
                    f"BMW API returned 403 – CarData API access not enabled. Response: {body}"
                )
            if resp.status == 429:
                raise RuntimeError("BMW API rate limit hit (50 calls/day exceeded)")
            if not resp.ok:
                body = await resp.text()
                _LOGGER.error("BMW API GET %s returned %s: %s", url, resp.status, body)
                resp.raise_for_status()
            return await resp.json()

    async def _post(self, path: str, json_body: Any) -> Any:
        await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        _LOGGER.debug("POST %s body=%s", url, json_body)
        async with self._session.post(url, json=json_body, headers=self._auth_headers()) as resp:
            if resp.status == 401:
                raise PermissionError("BMW API returned 401 – token may be revoked")
            if not resp.ok:
                body = await resp.text()
                _LOGGER.error("BMW API POST %s returned %s: %s", url, resp.status, body)
                resp.raise_for_status()
            return await resp.json()

    # ── Vehicle discovery ──────────────────────────────────────────────────────

    async def get_vehicle_mappings(self) -> list[dict[str, Any]]:
        """Return the list of VINs mapped to this account."""
        data = await self._get("/customers/vehicles/mappings")
        return data if isinstance(data, list) else []

    async def get_basic_data(self, vin: str) -> dict[str, Any]:
        """Return static vehicle metadata (model name, series, etc.)."""
        return await self._get(f"/customers/vehicles/{vin}/basicData")

    # ── Container management ──────────────────────────────────────────────────

    async def list_containers(self) -> list[dict[str, Any]]:
        """Return existing containers for this account."""
        data = await self._get("/customers/containers")
        return data if isinstance(data, list) else []

    async def create_container(
        self,
        name: str = CONTAINER_NAME,
        purpose: str = CONTAINER_PURPOSE,
        descriptors: list[str] = DESCRIPTORS,
    ) -> str:
        """Create a telemetry container and return its containerId."""
        body = {
            "name": name,
            "purpose": purpose,
            "technicalDescriptors": descriptors,
        }
        data = await self._post("/customers/containers", body)
        container_id: str = data["containerId"]
        _LOGGER.info("Created CarData container: %s", container_id)
        return container_id

    async def get_or_create_container(self) -> str:
        """Return an existing active container ID or create a new one.

        Reuses any existing ACTIVE container. If creation with our full
        descriptor list is rejected (400), retries with an empty list so the
        integration can still set up — descriptors can be configured in the
        BMW CarData portal afterward.
        """
        containers = await self.list_containers()
        _LOGGER.debug("Existing containers: %s", containers)

        for container in containers:
            if container.get("state") == "ACTIVE":
                _LOGGER.debug("Reusing existing container %s", container.get("containerId"))
                return container["containerId"]

        # Try with full descriptor list first
        try:
            return await self.create_container()
        except aiohttp.ClientResponseError as err:
            if err.status == 400:
                _LOGGER.warning(
                    "Container creation with full descriptor list rejected (400) – "
                    "retrying with empty list. Configure descriptors in the BMW portal. "
                    "Error: %s", err
                )
                return await self.create_container(descriptors=[])
            raise

    # ── Telemetry ─────────────────────────────────────────────────────────────

    async def get_telematics(self, vin: str, container_id: str) -> dict[str, dict[str, str]]:
        """Fetch latest telemetry for a VIN.

        Returns a dict keyed by descriptor ID, each value being
        {value, unit, timestamp}.
        """
        data = await self._get(
            f"/customers/vehicles/{vin}/telematicData",
            params={"containerId": container_id},
        )
        return data.get("telematicData", {})

    async def get_tyre_diagnosis(self, vin: str) -> dict[str, Any]:
        """Fetch Smart Maintenance tyre diagnosis for a VIN."""
        try:
            return await self._get(
                f"/customers/vehicles/{vin}/smartMaintenanceTyreDiagnosis"
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Tyre diagnosis unavailable for %s: %s", vin, err)
            return {}
