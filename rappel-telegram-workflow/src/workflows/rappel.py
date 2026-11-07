"""Workflow « rappel-telegram ».

Envoie un message sur Telegram via l'API Bot officielle
(POST https://api.telegram.org/bot<token>/sendMessage), pour être déclenché
par des schedules one-shot créés à la demande depuis Vibe.

Configuration (secrets du déploiement, jamais dans le code) :
- token du bot (@BotFather) : env TELEGRAM_BOT_TOKEN (ou telegram_bot_token) ;
- chat ID par défaut : env TELEGRAM_CHAT_ID (ou telegram_chat_id).

⚠️ Sandbox : ce module est chargé DANS le sandbox déterministe. Les imports
non déterministes (httpx, os, re) restent à l'intérieur des corps d'activité,
jamais en tête de module.
"""

from __future__ import annotations

from typing import Any

import mistralai.workflows as workflows
from pydantic import BaseModel, Field

TELEGRAM_API = "https://api.telegram.org"


class RappelInput(BaseModel):
    """Entrée du workflow : texte du rappel, chat éventuellement surchargé."""

    message: str = Field(min_length=1, max_length=4000)
    chat_id: str | None = None


class RappelResult(BaseModel):
    statut: str
    message_id: int | None = None


@workflows.activity(retry_policy_max_attempts=3, retry_policy_backoff_coefficient=2.0)
async def envoyer_message_telegram(message: str, chat_id: str | None) -> dict[str, Any]:
    """Activité : POST sendMessage sur l'API Bot Telegram."""
    import os
    import re

    import httpx

    token = (
        os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("telegram_bot_token") or ""
    ).strip()
    if not token:
        raise RuntimeError("Secret TELEGRAM_BOT_TOKEN absent du déploiement")
    if not re.fullmatch(r"\d{5,12}:[A-Za-z0-9_-]{20,}", token):
        # Ne divulgue que la longueur, jamais le contenu du secret.
        raise RuntimeError(
            f"TELEGRAM_BOT_TOKEN mal formé (longueur={len(token)}, "
            "format attendu '<id numérique>:<secret>')"
        )
    chat = (
        chat_id
        or os.environ.get("TELEGRAM_CHAT_ID")
        or os.environ.get("telegram_chat_id")
        or ""
    ).strip()
    if not chat:
        raise RuntimeError("chat_id absent (input ou secret TELEGRAM_CHAT_ID)")

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=30.0) as http:
        reponse = await http.post(url, json={"chat_id": chat, "text": message})
    if reponse.status_code == 401:
        bot_id, _, secret_part = token.partition(":")
        # Le bot_id n'est pas un credential (seule la partie après ':' l'est).
        raise RuntimeError(
            f"Telegram 401 (bot_id={bot_id}, longueur du secret={len(secret_part)}) : "
            "token révoqué ou faux — régénérer via @BotFather (/mybots → /revoke), "
            "mettre à jour le secret Studio, puis redémarrer le déploiement"
        )
    if reponse.status_code != 200:
        raise RuntimeError(f"Telegram HTTP {reponse.status_code}: {reponse.text[:200]}")
    corps = reponse.json()
    if not corps.get("ok"):
        raise RuntimeError(f"Telegram ok=false: {str(corps)[:200]}")
    print(f"Message Telegram envoyé (message_id={corps['result']['message_id']})")
    return {"statut": "ok", "message_id": corps["result"]["message_id"]}


@workflows.workflow.define(
    name="rappel-telegram",
    workflow_display_name="Rappel Telegram",
    workflow_description=(
        "Envoie un message sur Telegram via l'API Bot (sendMessage). "
        "Déclenché par des schedules one-shot créés à la demande depuis Vibe."
    ),
)
class RappelTelegramWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: RappelInput) -> RappelResult:
        donnees = await envoyer_message_telegram(input.message, input.chat_id)
        return RappelResult(**donnees)
