"""Workflow « releve-energie-maison » (Auvers-sur-Oise).

Relevé quotidien du compteur d'énergie de la maison d'Auvers-sur-Oise via
l'app SmartThings « Vibe » (lecture seule). Silencieux en cas de succès :
aucune notification, uniquement une ligne ajoutée au CSV.

Comportement :
- lit les jetons et le CSV depuis la library Mistral « maison-connectee » ;
- lit le compteur (main.energy.value en kWh cumulés, main.power.value en watts) ;
- si 401 : refresh OAuth puis persistance IMMÉDIATE des nouveaux jetons
  (le refresh token est à usage unique, la chaîne casse sans cette écriture) ;
- ajoute une ligne `<horodatage UTC ISO 8601 Z>;<kwh>;<watts>` au CSV ;
- en cas d'échec complet après essais : ligne `<horodatage>;ERREUR;<motif>`
  (jamais de trou silencieux) ;
- l'activité est idempotente (retry SDK sans doublon de ligne).
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import mistralai.workflows as workflows
from pydantic import BaseModel

from workflows import smartthings, state_store

LIBRARY_NAME = os.environ.get("MAISON_LIBRARY_NAME", "maison-connectee")
CSV_DOC = "releves-energie.csv"
TOKENS_DOC = "smartthings-tokens.json"
CREDENTIALS_DOC = "smartthings-credentials.json"
CSV_HEADER = "horodatage;kwh_cumules;watts"

NB_ESSAIS_LECTURE = 3
ANTI_DOUBLON_MINUTES = 15


class ReleveInput(BaseModel):
    """Entrée du workflow (le champ source sert uniquement à la traçabilité)."""

    source: str = "schedule"


class ReleveResult(BaseModel):
    statut: str
    horodatage: str
    kwh_cumules: str | None = None
    watts: str | None = None
    erreur: str | None = None


def _motif(exc: Exception) -> str:
    """Motif court, sans point-virgule ni retour ligne, pour la ligne ERREUR."""
    texte = f"{type(exc).__name__}: {exc}"
    texte = texte.replace(";", ",").replace("\n", " ").replace("\r", " ")
    return texte[:80]


def _sanitiser_csv(csv_text: str) -> list[str]:
    """Lignes non vides du CSV ; l'en-tête est ajouté s'il est absent."""
    lignes = [l.strip() for l in (csv_text or "").splitlines() if l.strip()]
    if not lignes or not lignes[0].lower().startswith("horodatage"):
        lignes.insert(0, CSV_HEADER)
    return lignes


def _est_doublon_recent(lignes: list[str], kwh: str, watts: str, maintenant: datetime) -> bool:
    """Vrai si la dernière ligne contient déjà ces valeurs (relevé < 15 min)."""
    if len(lignes) < 2:
        return False
    champs = lignes[-1].split(";")
    if len(champs) != 3 or champs[1] != kwh or champs[2] != watts:
        return False
    try:
        derniere = datetime.strptime(champs[0], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return False
    return (maintenant - derniere) < timedelta(minutes=ANTI_DOUBLON_MINUTES)


async def _lecture(
    http: httpx.AsyncClient,
    creds: dict[str, str],
    tokens: dict[str, str],
    lib_id: str,
    device_id: str | None = None,
) -> tuple[str, str, dict[str, str]]:
    """Lit le compteur, avec refresh sur 401 et persistance immédiate des jetons.

    Retourne (kwh, watts, jetons_utilisés) ou lève la dernière erreur.
    """
    device_id = device_id or os.environ.get("MAISON_ENERGY_DEVICE_ID")
    if not device_id:
        raise RuntimeError("deviceId absent (credentials ou MAISON_ENERGY_DEVICE_ID)")
    derniere_erreur: Exception | None = None
    for essai in range(NB_ESSAIS_LECTURE):
        try:
            kwh, watts = await smartthings.lire_etat_compteur(
                http, tokens["access_token"], device_id
            )
            return kwh, watts, tokens
        except smartthings.UnauthorisedError:
            # access token expiré : refresh + persistance IMMÉDIATE
            tokens = await smartthings.rafraichir_jetons(
                http, creds["oauthClientId"], creds["oauthClientSecret"],
                tokens["refresh_token"],
            )
            tokens["obtained_at"] = state_store.maintenant_utc()
            await state_store.ecrire_document(
                http, lib_id, TOKENS_DOC, json.dumps(tokens, indent=2).encode()
            )
            print("Jetons SmartThings rafraîchis et persistés.")
            derniere_erreur = None
        except Exception as exc:  # transport, 5xx, réessai
            derniere_erreur = exc
            if essai < NB_ESSAIS_LECTURE - 1:
                await asyncio.sleep(2 ** essai)
    assert derniere_erreur is not None
    raise derniere_erreur


@workflows.activity(retry_policy_max_attempts=3, retry_policy_backoff_coefficient=2.0)
async def faire_le_releve() -> dict[str, Any]:
    """Activité complète : chargement de l'état, lecture, persistance.

    Idempotente en cas de retry SDK : re-lit l'état depuis la library et ne
    réécrit pas une ligne déjà présente (garde anti-doublon).
    """
    horodatage = state_store.maintenant_utc()
    maintenant = datetime.now(timezone.utc)
    lib_id: str | None = None

    async with httpx.AsyncClient(base_url=state_store.MISTRAL_API, timeout=60.0) as http:
        lib_id = await state_store.trouver_ou_creer_library(http, LIBRARY_NAME)

        creds_brut = await state_store.lire_texte(http, lib_id, CREDENTIALS_DOC)
        if not creds_brut:
            raise RuntimeError(
                f"Document {CREDENTIALS_DOC} introuvable dans la library {LIBRARY_NAME}"
            )
        creds = json.loads(creds_brut)

        device_id = creds.get("deviceId") or creds.get("energyMeterDeviceId")

        tokens_brut = await state_store.lire_texte(http, lib_id, TOKENS_DOC)
        if not tokens_brut:
            raise RuntimeError(
                f"Document {TOKENS_DOC} introuvable dans la library {LIBRARY_NAME}"
            )
        tokens = json.loads(tokens_brut)

        csv_texte = await state_store.lire_texte(http, lib_id, CSV_DOC, defaut="")

        try:
            kwh, watts, _ = await _lecture(http, creds, tokens, lib_id, device_id)
            ligne = f"{horodatage};{kwh};{watts}"
            lignes = _sanitiser_csv(csv_texte)
            if not _est_doublon_recent(lignes, kwh, watts, maintenant):
                lignes.append(ligne)
                await state_store.ecrire_document(
                    http, lib_id, CSV_DOC, ("\n".join(lignes) + "\n").encode()
                )
            print(f"Relevé OK: {ligne}")
            return {
                "statut": "ok",
                "horodatage": horodatage,
                "kwh_cumules": kwh,
                "watts": watts,
            }
        except Exception as exc:
            motif = _motif(exc)
            ligne = f"{horodatage};ERREUR;{motif}"
            lignes = _sanitiser_csv(csv_texte)
            if lignes[-1] != ligne:
                lignes.append(ligne)
                await state_store.ecrire_document(
                    http, lib_id, CSV_DOC, ("\n".join(lignes) + "\n").encode()
                )
            print(f"Relevé en ERREUR: {ligne}")
            return {
                "statut": "erreur",
                "horodatage": horodatage,
                "erreur": motif,
            }


@workflows.workflow.define(
    name="releve-energie-maison",
    workflow_display_name="Relevé énergie maison",
    workflow_description=(
        "Relève quotidien du compteur d'énergie SmartThings (Auvers-sur-Oise), "
        "lecture seule sans notification : ajoute une ligne au CSV releves-energie."
    ),
)
class ReleveEnergieWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: ReleveInput) -> ReleveResult:
        donnees = await faire_le_releve()
        return ReleveResult(**donnees)
