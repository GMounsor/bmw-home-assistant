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
    ICE_DESCRIPTORS,
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
                # BMW returns rate-limit errors as 403 with CU-429 in the body
                if "CU-429" in body:
                    _LOGGER.error("BMW API rate limit reached (50 calls/day). Response: %s", body)
                    raise RuntimeError("BMW API rate limit reached (50 calls/day). Try again tomorrow.")
                _LOGGER.error("BMW API 403 for %s - CarData API not enabled. Response: %s", url, body)
                raise PermissionError(f"BMW API 403 - access not enabled: {body}")
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

    async def delete_container(self, container_id):
        await self._ensure_token()
        url = f"{API_BASE_URL}/customers/containers/{container_id}"
        _LOGGER.debug("DELETE %s", url)
        async with self._session.delete(url, headers=self._auth_headers()) as resp:
            if not resp.ok:
                body = await resp.text()
                _LOGGER.warning("DELETE container %s returned %s: %s", container_id, resp.status, body)

    async def get_or_create_container(self):
        """Return (or create) the container matching CONTAINER_NAME.

        Reuses an existing container whose name matches CONTAINER_NAME.
        If none exists, deletes ALL stale containers first (BMW enforces a
        low per-account container limit) then creates a fresh one.
        """
        containers = await self.list_containers()
        _LOGGER.debug("Existing containers: %s", containers)

        # Reuse our named container if it already exists
        for container in containers:
            if container.get("state") == "ACTIVE" and container.get("name") == CONTAINER_NAME:
                _LOGGER.debug("Reusing container %s (%s)", CONTAINER_NAME, container.get("containerId"))
                return container["containerId"]

        # Clean up stale / old-named containers to stay within BMW's limit
        for container in containers:
            cid = container.get("containerId")
            cname = container.get("name", "")
            if cid and cname != CONTAINER_NAME:
                _LOGGER.info("Deleting stale container '%s' (%s)", cname, cid)
                await self.delete_container(cid)

        # 3-tier fallback: full list → ICE-only → no descriptors
        try:
            return await self.create_container(descriptors=DESCRIPTORS)
        except aiohttp.ClientResponseError as err:
            if err.status != 400:
                raise
            _LOGGER.warning("Full descriptor list rejected (400); trying ICE-only list")

        try:
            return await self.create_container(descriptors=ICE_DESCRIPTORS)
        except aiohttp.ClientResponseError as err:
            if err.status != 400:
                raise
            _LOGGER.warning("ICE descriptor list also rejected (400); creating without descriptors")

        return await self.create_container(descriptors=None)

    async def get_telematics(self, vin, container_id):
        data = await self._get(
            f"/customers/vehicles/{vin}/telematicData",
            params={"containerId": container_id},
        )
        telematics = data.get("telematicData", {})
        _LOGGER.debug(
            "Raw telematicData type=%s sample=%s",
            type(telematics).__name__,
            str(telematics)[:500],
        )
        # BMW returns a list: [{descriptor, value, unit, timestamp}, ...]
        # Convert to dict keyed by descriptor for sensor lookups
        if isinstance(telematics, list):
            return {
                item["descriptor"]: {k: v for k, v in item.items() if k != "descriptor"}
                for item in telematics
                if "descriptor" in item
            }
        return telematics

    async def get_tyre_diagnosis(self, vin):
        try:
            return await self._get(f"/customers/vehicles/{vin}/smartMaintenanceTyreDiagnosis")
        except Exception as err:
            _LOGGER.warning("Tyre diagnosis unavailable for %s: %s", vin, err)
            return {}
