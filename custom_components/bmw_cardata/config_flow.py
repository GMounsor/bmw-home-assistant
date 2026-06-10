"""Config flow for BMW CarData integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import BMWCarDataAPI
from .auth import DeviceFlowData, TokenData, initiate_device_flow, poll_for_token
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CONTAINER_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    CONF_VINS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class BMWCarDataConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle BMW CarData config flow.

    Steps:
        user       → Enter Client ID
        authorize  → Visit verification URL, then click Submit
        (internal) → Poll for token, discover VINs, create entry
    """

    VERSION = 1

    def __init__(self) -> None:
        self._client_id: str = ""
        self._device_flow: DeviceFlowData | None = None
        self._session: aiohttp.ClientSession | None = None

    # ── Step 1: Client ID ─────────────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID].strip()

            # Basic UUID-ish validation
            if not self._client_id or len(self._client_id) < 8:
                errors[CONF_CLIENT_ID] = "invalid_client_id"
            else:
                try:
                    self._session = aiohttp.ClientSession()
                    self._device_flow = await initiate_device_flow(
                        self._session, self._client_id
                    )
                    return await self.async_step_authorize()
                except Exception as err:  # noqa: BLE001
                    _LOGGER.exception("Device flow initiation failed")
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_CLIENT_ID): str}),
            errors=errors,
            description_placeholders={
                "portal_url": "https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration_Step-1"
            },
        )

    # ── Step 2: Device Authorization ─────────────────────────────────────────

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        flow = self._device_flow

        if flow is None:
            return await self.async_step_user()

        if user_input is not None:
            # User clicked Submit – try polling for token once
            try:
                token = await poll_for_token(
                    self._session,
                    self._client_id,
                    flow.device_code,
                    flow.code_verifier,
                )
            except ValueError as err:
                _LOGGER.error("Token poll error: %s", err)
                errors["base"] = "auth_failed"
                token = None

            if token is None and not errors:
                errors["base"] = "authorization_pending"

            if token is not None:
                return await self._create_entry(token)

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({}),  # No inputs – just a Submit button
            errors=errors,
            description_placeholders={
                "user_code": flow.user_code,
                "verification_url": flow.verification_uri_complete,
            },
        )

    # ── Entry creation ────────────────────────────────────────────────────────

    async def _create_entry(self, token: TokenData) -> FlowResult:
        """Discover VINs and container, then create the config entry."""
        api = BMWCarDataAPI(self._session, self._client_id, token)

        try:
            mappings = await api.get_vehicle_mappings()
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Failed to fetch vehicle mappings")
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")

        vins = [m["vin"] for m in mappings if m.get("mappingType") in ("PRIMARY", None)]

        if not vins:
            if self._session:
                await self._session.close()
            return self.async_abort(reason="no_vehicles")

        try:
            container_id = await api.get_or_create_container()
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Failed to create telemetry container")
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")

        if self._session:
            await self._session.close()

        # Use first VIN to generate a unique entry ID
        await self.async_set_unique_id(vins[0])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"BMW ({', '.join(vins)})",
            data={
                CONF_CLIENT_ID: self._client_id,
                CONF_ACCESS_TOKEN: token.access_token,
                CONF_REFRESH_TOKEN: token.refresh_token,
                CONF_TOKEN_EXPIRES_AT: token.expires_at,
                CONF_CONTAINER_ID: container_id,
                CONF_VINS: vins,
            },
        )
