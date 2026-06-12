"""BMW CarData OAuth2 Device Authorization Grant (with PKCE)."""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

from .const import (
    DEVICE_CODE_URL,
    GRANT_TYPE_DEVICE,
    OAUTH_SCOPE,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


# ── PKCE helpers ──────────────────────────────────────────────────────────────

def _generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE S256."""
    # RFC 7636: verifier is 43-128 URL-safe chars
    verifier_bytes = os.urandom(48)  # 48 bytes → 64 base64url chars
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DeviceFlowData:
    """Response from the device code endpoint."""
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int
    code_verifier: str   # stored so we can complete the PKCE token exchange


@dataclass
class TokenData:
    """Access + refresh tokens with expiry."""
    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp


# ── Public functions ──────────────────────────────────────────────────────────

async def initiate_device_flow(
    session: aiohttp.ClientSession,
    client_id: str,
) -> DeviceFlowData:
    """Start device authorization flow.

    Returns a DeviceFlowData with the URL/code to show the user.
    Raises aiohttp.ClientError or ValueError on failure.
    """
    code_verifier, code_challenge = _generate_pkce_pair()

    payload = {
        "client_id": client_id,
        "response_type": "device_code",
        "scope": OAUTH_SCOPE,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    _LOGGER.debug("Initiating device flow for client_id=%s", client_id)
    async with session.post(
        DEVICE_CODE_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as resp:
        if resp.status != 200:
            body = await resp.text()
            raise ValueError(f"Device code request failed ({resp.status}): {body}")
        data: dict[str, Any] = await resp.json()

    return DeviceFlowData(
        device_code=data["device_code"],
        user_code=data["user_code"],
        verification_uri=data["verification_uri"],
        verification_uri_complete=data.get(
            "verification_uri_complete",
            f"{data['verification_uri']}?user_code={data['user_code']}",
        ),
        expires_in=data["expires_in"],
        interval=data.get("interval", 5),
        code_verifier=code_verifier,
    )


async def poll_for_token(
    session: aiohttp.ClientSession,
    client_id: str,
    device_code: str,
    code_verifier: str,
) -> TokenData | None:
    """Poll the token endpoint once.

    Returns TokenData on success.
    Returns None if authorization is still pending.
    Raises ValueError on hard errors (expired, denied, invalid_client).
    """
    payload = {
        "client_id": client_id,
        "grant_type": GRANT_TYPE_DEVICE,
        "device_code": device_code,
        "code_verifier": code_verifier,
    }

    async with session.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as resp:
        data: dict[str, Any] = await resp.json(content_type=None)

        if resp.status == 200:
            return TokenData(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=time.time() + data.get("expires_in", 3600),
            )

        error = data.get("error", "")

        if error in ("authorization_pending",):
            return None  # user hasn't authorized yet – keep polling

        if error == "slow_down":
            return None  # caller should wait longer before retrying

        # Hard errors
        raise ValueError(f"Token exchange failed: {error} – {data.get('error_description', '')}")


async def refresh_access_token(
    session: aiohttp.ClientSession,
    client_id: str,
    refresh_token: str,
) -> TokenData:
    """Use a refresh token to obtain a new access token.

    Raises ValueError if the refresh token is no longer valid.
    """
    payload = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": OAUTH_SCOPE,  # BMW requires scope even on refresh requests
    }

    async with session.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as resp:
        data: dict[str, Any] = await resp.json(content_type=None)

        if resp.status == 200:
            return TokenData(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                expires_at=time.time() + data.get("expires_in", 3600),
            )

        raise PermissionError(
            f"Token refresh failed ({resp.status}): {data.get('error', 'unknown')}"
        )
