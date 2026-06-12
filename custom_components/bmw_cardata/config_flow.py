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
    CONF_ALL_VINS,
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
        user        → Enter Client ID
        authorize   → Visit verification URL, then click Submit
        select_vins → Choose which vehicles to monitor
    """

    VERSION = 1

    def __init__(self) -> None:
        self._client_id: str = ""
        self._device_flow: DeviceFlowData | None = None
        self._session: aiohttp.ClientSession | None = None
        self._token: TokenData | None = None
        self._all_vins: list[str] = []
        self._container_id: str = ""

    # ── Step 1: Client ID ─────────────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID].strip()

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
                self._token = token
                return await self._discover_vehicles()

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "user_code": flow.user_code,
                "verification_url": flow.verification_uri_complete,
            },
        )

    # ── Step 3: Discover vehicles & select VINs ───────────────────────────────

    async def _discover_vehicles(self) -> FlowResult:
        """Fetch VIN list and container, then show VIN selection."""
        api = BMWCarDataAPI(self._session, self._client_id, self._token)

        try:
            mappings = await api.get_vehicle_mappings()
        except PermissionError as err:
            _LOGGER.error("BMW API 403 during setup: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="api_not_enabled")
        except RuntimeError as err:
            if "rate limit" in str(err).lower():
                _LOGGER.error("BMW rate limit during setup: %s", err)
                if self._session:
                    await self._session.close()
                return self.async_abort(reason="rate_limit")
            _LOGGER.exception("Failed to fetch vehicle mappings: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Failed to fetch vehicle mappings: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")

        self._all_vins = [m["vin"] for m in mappings if m.get("vin")]
        if not self._all_vins:
            if self._session:
                await self._session.close()
            return self.async_abort(reason="no_vehicles")

        try:
            self._container_id = await api.get_or_create_container()
            self._token = api.get_current_token()
        except PermissionError as err:
            _LOGGER.error("BMW API 403 creating container: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="api_not_enabled")
        except RuntimeError as err:
            if "rate limit" in str(err).lower():
                if self._session:
                    await self._session.close()
                return self.async_abort(reason="rate_limit")
            _LOGGER.exception("Failed to create container: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Failed to create container: %s", err)
            if self._session:
                await self._session.close()
            return self.async_abort(reason="cannot_connect")

        if self._session:
            await self._session.close()

        return await self.async_step_select_vins()

    async def async_step_select_vins(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user choose which VINs to monitor."""
        if user_input is not None:
            selected = [vin for vin in self._all_vins if user_input.get(vin)]
            if not selected:
                return self.async_show_form(
                    step_id="select_vins",
                    data_schema=self._vin_schema(self._all_vins),
                    errors={"base": "no_vins_selected"},
                )

            await self.async_set_unique_id(self._all_vins[0])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"BMW ({', '.join(selected)})",
                data={
                    CONF_CLIENT_ID: self._client_id,
                    CONF_ACCESS_TOKEN: self._token.access_token,
                    CONF_REFRESH_TOKEN: self._token.refresh_token,
                    CONF_TOKEN_EXPIRES_AT: self._token.expires_at,
                    CONF_CONTAINER_ID: self._container_id,
                    CONF_ALL_VINS: self._all_vins,   # all discovered VINs (for options flow)
                    CONF_VINS: selected,              # currently active VINs
                },
            )

        return self.async_show_form(
            step_id="select_vins",
            data_schema=self._vin_schema(self._all_vins, default_all=True),
        )

    @staticmethod
    def _vin_schema(vins: list[str], default_all: bool = True) -> vol.Schema:
        return vol.Schema({
            vol.Optional(vin, default=default_all): bool
            for vin in vins
        })

    @staticmethod
    def async_get_options_flow(config_entry):
        return BMWCarDataOptionsFlow(config_entry)


class BMWCarDataOptionsFlow(config_entries.OptionsFlow):
    """Allow changing the active VIN set after initial setup."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        all_vins = self._config_entry.data.get(CONF_ALL_VINS, self._config_entry.data.get(CONF_VINS, []))
        active_vins = self._config_entry.options.get(CONF_VINS, self._config_entry.data.get(CONF_VINS, []))

        if user_input is not None:
            selected = [vin for vin in all_vins if user_input.get(vin)]
            if not selected:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._vin_schema(all_vins, active_vins),
                    errors={"base": "no_vins_selected"},
                )
            return self.async_create_entry(data={CONF_VINS: selected})

        return self.async_show_form(
            step_id="init",
            data_schema=self._vin_schema(all_vins, active_vins),
        )

    @staticmethod
    def _vin_schema(all_vins: list[str], active_vins: list[str]) -> vol.Schema:
        return vol.Schema({
            vol.Optional(vin, default=(vin in active_vins)): bool
            for vin in all_vins
        })
