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
    CONTAINER_NAME,
    CONTAINER_PURPOSE,
    DESCRIPTORS,
    TOKEN_REFRESH_BUFFER_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


class BMWCarDataAPI:

    def __init__(self, session, client_id, token):
        self._session = session
        self._client_id = client_id
        self._token = token

    async def _ensure_token(self):
        if time.time() >= self._token.expires_at - TOKEN_REFRESH_BUFFER_SECONDS:
            _LOGGER.debug("Refreshing access token")
            self._token = await refresh_access_token(
                self._session, self._client_id, self._token.refresh_token
            )

    def get_current_token(self):
        return self._token

    def _auth_headers(self):
        return {**API_VERSION_HEADER, "Authorization": f"Bearer {self._token.access_token}"}

    async def _get(self, path, **kwargs):
        await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        _LOGGER.debug("GET %s", url)
        async with self._session.get(url, headers=self._auth_headers(), **kwargs) as resp:
            if resp.status == 401:
                raise PermissionError("BMW API 401 - token revoked")
            if resp.status == 403:
                body = await resp.text()
                _LOGGER.error("BMW API 403 for %s - CarData API not enabled in portal. Response: %s", url, body)
                raise PermissionError(f"BMW API 403 - CarData API access not enabled: {body}")
            if resp.status == 429:
                raise RuntimeError("BMW API rate limit hit (50 calls/day exceeded)")
            if not resp.ok:
                body = await resp.text()
                _LOGGER.error("BMW API GET %s returned %s: %s", url, resp.status, body)
                resp.raise_for_status()
            return await resp.json()

    async def _post(self, path, json_body):
        await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        _LOGGER.debug("POST %s body=%s", url, json_body)
        async with self._session.post(url, json=json_body, headers=self._auth_headers()) as resp:
            if resp.status == 401:
                raise PermissionError("BMW API 401 - token revoked")
            if not resp.ok:
                body = await resp.text()
                _LOGGER.error("BMW API POST %s returned %s: %s", url, resp.status, body)
                resp.raise_for_status()
            return await resp.json()

    async def get_vehicle_mappings(self):
        data = await self._get("/customers/vehicles/mappings")
        return data if isinstance(data, list) else []

    async def get_basic_data(self, vin):
        return await self._get(f"/customers/vehicles/{vin}/basicData")

    async def list_containers(self):
        data = await self._get("/customers/containers")
        return data if isinstance(data, list) else []

    async def create_container(self, name=CONTAINER_NAME, purpose=CONTAINER_PURPOSE, descriptors=None):
        body = {"name": name, "purpose": purpose}
        if descriptors:
            body["technicalDescriptors"] = descriptors
        _LOGGER.debug("Creating container with body: %s", body)
        data = await self._post("/customers/containers", body)
        container_id = data["containerId"]
        _LOGGER.info("Created CarData container: %s", container_id)
        return container_id

    async def get_or_create_container(self):
        containers = await self.list_containers()
        _LOGGER.debug("Existing containers: %s", containers)

        for container in containers:
            if container.get("state") == "ACTIVE":
                _LOGGER.debug("Reusing existing container %s", container.get("containerId"))
                return container["containerId"]

        # Try with descriptor list first
        try:
            return await self.create_container(descriptors=DESCRIPTORS)
        except aiohttp.ClientResponseError as err:
            if err.status != 400:
                raise
            _LOGGER.warning(
                "Container creation with descriptor list rejected (400) - "
                "retrying without descriptors (BMW will use portal-configured set). "
                "Error: %s", err
            )

        # Fallback: omit technicalDescriptors entirely
        return await self.create_container(descriptors=None)

    async def get_telematics(self, vin, container_id):
        data = await self._get(
            f"/customers/vehicles/{vin}/telematicData",
            params={"containerId": container_id},
        )
        return data.get("telematicData", {})

    async def get_tyre_diagnosis(self, vin):
        try:
            return await self._get(f"/customers/vehicles/{vin}/smartMaintenanceTyreDiagnosis")
        except Exception as err:
            _LOGGER.warning("Tyre diagnosis unavailable for %s: %s", vin, err)
            return {}
