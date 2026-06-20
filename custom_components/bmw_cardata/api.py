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
        _LOGGER.debug("list_containers raw response: type=%s value=%s", type(data).__name__, str(data)[:500])
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # BMW may wrap the list under "containers", "data", "items" etc.
            for key in ("containers", "data", "items", "content"):
                if isinstance(data.get(key), list):
                    _LOGGER.debug("Unwrapping containers from key '%s'", key)
                    return data[key]
        _LOGGER.warning("Unexpected list_containers response shape: %s", data)
        return []

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

    async def _delete_all_containers(self, containers):
        """Delete every container in the list, logging each one."""
        for container in containers:
            cid = container.get("containerId")
            cname = container.get("name", "unknown")
            if cid:
                _LOGGER.info("Deleting container '%s' (%s)", cname, cid)
                await self.delete_container(cid)

    async def get_or_create_container(self):
        """Return (or create) the container matching CONTAINER_NAME.

        Reuses an existing container whose name matches CONTAINER_NAME.
        Otherwise deletes stale containers (BMW has a low per-account limit)
        and creates a new one, with 3-tier descriptor fallback.
        If BMW returns CU-124 (limit still reached), force-deletes ALL
        containers and retries.
        """
        containers = await self.list_containers()
        _LOGGER.debug("Found %d containers", len(containers))

        # Reuse our named container if it exists
        for container in containers:
            if container.get("state") == "ACTIVE" and container.get("name") == CONTAINER_NAME:
                _LOGGER.debug("Reusing container %s (%s)", CONTAINER_NAME, container.get("containerId"))
                return container["containerId"]

        # Delete containers that don't match our current name
        stale = [c for c in containers if c.get("name") != CONTAINER_NAME]
        if stale:
            _LOGGER.info("Deleting %d stale container(s)", len(stale))
            await self._delete_all_containers(stale)

        # 2-tier creation fallback: full (ICE+EV) → ICE-only
        # NOTE: BMW rejects containers with no descriptors (CU-401), so there is
        # no safe empty-descriptor fallback — ICE_DESCRIPTORS is the last resort.
        for descriptor_list, label in [
            (DESCRIPTORS, "full"),
            (ICE_DESCRIPTORS, "ICE-only"),
        ]:
            try:
                container_id = await self.create_container(descriptors=descriptor_list)
                _LOGGER.info("Container created with %s descriptor list (%d descriptors)", label, len(descriptor_list or []))
                return container_id
            except aiohttp.ClientResponseError as err:
                if err.status == 403:
                    # CU-124: BMW still says limit reached – force-delete everything and retry once
                    _LOGGER.warning(
                        "CU-124 on creation with %s descriptors; force-deleting all containers and retrying",
                        label,
                    )
                    all_containers = await self.list_containers()
                    await self._delete_all_containers(all_containers)
                    try:
                        return await self.create_container(descriptors=descriptor_list)
                    except aiohttp.ClientResponseError as retry_err:
                        _LOGGER.warning("Retry still failed (%s), trying next fallback", retry_err.status)
                        continue
                if err.status != 400:
                    raise
                _LOGGER.warning("%s descriptor list rejected (400); trying next fallback", label)

        raise RuntimeError("All container creation attempts failed — ICE descriptor list was also rejected")

    async def get_telematics(self, vin, container_id):
        _LOGGER.debug("Fetching telemetry for VIN %s using container %s", vin, container_id)
        data = await self._get(
            f"/customers/vehicles/{vin}/telematicData",
            params={"containerId": container_id},
        )
        telematics = data.get("telematicData", {})
        # BMW returns a list: [{descriptor, value, unit, timestamp}, ...]
        # Convert to dict keyed by descriptor for sensor lookups
        if isinstance(telematics, list):
            result = {
                item["descriptor"]: {k: v for k, v in item.items() if k != "descriptor"}
                for item in telematics
                if "descriptor" in item
            }
            _LOGGER.debug(
                "Telemetry for VIN %s — %d descriptors returned: %s",
                vin,
                len(result),
                sorted(result.keys()),
            )
            return result
        if isinstance(telematics, dict):
            _LOGGER.debug(
                "Telemetry for VIN %s — %d descriptors returned: %s",
                vin,
                len(telematics),
                sorted(telematics.keys()),
            )
        else:
            _LOGGER.debug("Raw telematicData (non-list/dict) type=%s: %s", type(telematics).__name__, str(telematics)[:500])
        return telematics

    async def get_tyre_diagnosis(self, vin):
        try:
            return await self._get(f"/customers/vehicles/{vin}/smartMaintenanceTyreDiagnosis")
        except Exception as err:
            _LOGGER.warning("Tyre diagnosis unavailable for %s: %s", vin, err)
            return {}
