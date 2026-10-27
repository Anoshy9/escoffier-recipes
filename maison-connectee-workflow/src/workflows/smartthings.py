"""Client SmartThings (lecture seule) : état du compteur + refresh OAuth.

L'app OAuth « Vibe » (scope r:devices:*) fournit :
- access_token : 24 h
- refresh_token : 30 jours, renouvelé à chaque usage (usage unique).
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

ST_BASE = "https://api.smartthings.com"
DEVICE_STATES_PATH = "/v1/devices/{device_id}/states"
OAUTH_TOKEN_PATH = "/oauth/token"


class UnauthorisedError(RuntimeError):
    """401 renvoyé par l'API SmartThings (access token expiré/invalid)."""


def _basic_auth(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def _extraire_valeurs(payload: dict[str, Any]) -> tuple[str, str]:
    """Extrait (kwh_cumulés, watts) depuis la réponse /states."""
    main = payload.get("main", {})
    energy = main.get("energy", {}).get("value")
    power = main.get("power", {}).get("value")
    if energy is None or power is None:
        raise RuntimeError(f"Champs energy/power absents: {payload}")
    return str(energy), str(power)


async def lire_etat_compteur(
    http: httpx.AsyncClient, access_token: str, device_id: str
) -> tuple[str, str]:
    """Lit main.energy.value (kWh cumulés) et main.power.value (watts). Lève UnauthorisedError si 401."""
    resp = await http.get(
        ST_BASE + DEVICE_STATES_PATH.format(device_id=device_id),
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code == 401:
        raise UnauthorisedError("401 SmartThings")
    resp.raise_for_status()
    return _extraire_valeurs(resp.json())


async def rafraichir_jetons(
    http: httpx.AsyncClient,
    oauth_client_id: str,
    oauth_client_secret: str,
    refresh_token: str,
) -> dict[str, str]:
    """POST /oauth/token (grant_type=refresh_token). Retourne les nouveaux jetons.

    Le refresh token est renouvelé à chaque usage : le résultat DOIT être
    persisté immédiatement, sans quoi la chaîne casse.
    """
    resp = await http.post(
        ST_BASE + OAUTH_TOKEN_PATH,
        headers={"Authorization": _basic_auth(oauth_client_id, oauth_client_secret)},
        data={
            "grant_type": "refresh_token",
            "client_id": oauth_client_id,
            "refresh_token": refresh_token,
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Refresh OAuth en échec (HTTP {resp.status_code}): {resp.text[:200]}")
    data = resp.json()
    if not data.get("access_token") or not data.get("refresh_token"):
        raise RuntimeError(f"Réponse refresh incomplète: {data}")
    return data
