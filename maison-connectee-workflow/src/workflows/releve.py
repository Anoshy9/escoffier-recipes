"""Workflow « releve-energie-maison » (Auvers-sur-Oise).

Relevé quotidien du compteur d'énergie de la maison d'Auvers-sur-Oise via
l'app SmartThings « Vibe » (lecture seule). Silencieux en cas de succès :
aucune notification, uniquement une ligne ajoutée au CSV.

Deux modes :

1. Mode autonome (planifié, « source » seul en entrée) : lit les jetons et
   le CSV depuis la library Mistral « maison-connectee » via l'API REST
   Libraries (nécessite MAISON_API_KEY liée au déploiement), lit le compteur,
   persiste jetons et CSV. C'est le mode nominal.

2. Mode délégué (entrée avec credentials/tokens/uploads fournis) :
   l'appelant gère l'état et la persistance. Le worker lit le compteur,
   rafraîchit les jetons sur 401, compose la ligne CSV (relevé ou ERREUR)
   et téléverse CSV + jetons vers des URLs pré-signées préparées par
   l'appelant (action « prepare » de l'API Libraries) — aucun appel
   authentifié à l'API Mistral depuis le worker. Contournement du 401
   « User id is required » du token de service-account tant que la clé
   MAISON_API_KEY n'est pas liée au déploiement.

Comportements clés :
- main.energy.value en kWh cumulés, main.power.value en watts ;
- si 401 : refresh OAuth, jetons rafraîchis retournés pour persistance
  IMMÉDIATE par l'appelant (le refresh token est à usage unique) ;
- ligne « horodatage;kwh;watts » ou « horodatage;ERREUR;motif »
  (jamais de trou silencieux).

Attention sandbox : ce module définit la classe de workflow, il est chargé
DANS le sandbox déterministe. Les imports non déterministes (httpx, os,
modules d'I/O) doivent rester à l'intérieur des corps de fonction
d'activité, jamais en tête de module.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import mistralai.workflows as workflows
from pydantic import BaseModel

CSV_DOC = "releves-energie.csv"
TOKENS_DOC = "smartthings-tokens.json"
CREDENTIALS_DOC = "smartthings-credentials.json"
CSV_HEADER = "horodatage;kwh_cumules;watts"

NB_ESSAIS_LECTURE = 3
ANTI_DOUBLON_MINUTES = 15


class ReleveInput(BaseModel):
    """Entrée du workflow.

    - source : traçabilité uniquement.
    - Mode autonome : credentials/tokens/csv_lignes/uploads absents.
    - Mode délégué : credentials et tokens fournis ; csv_lignes (lignes
      existantes du CSV, en-tête compris, sans la nouvelle ligne) et
      uploads (requêtes pré-signées csv/tokens produites par l'action
      « prepare » de l'API Libraries) optionnels — sans uploads, lecture
      seule sans persistance côté worker.
    """

    source: str = "schedule"
    credentials: dict[str, Any] | None = None
    tokens: dict[str, Any] | None = None
    csv_lignes: list[str] | None = None
    uploads: dict[str, Any] | None = None


class ReleveResult(BaseModel):
    statut: str
    horodatage: str
    kwh_cumules: str | None = None
    watts: str | None = None
    erreur: str | None = None
    jetons: dict[str, Any] | None = None
    uploads_rapport: dict[str, Any] | None = None


def _utcnow_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    http: Any,
    creds: dict[str, str],
    tokens: dict[str, str],
    lib_id: str,
    device_id: str,
    st: Any,
    store: Any,
) -> tuple[str, str, dict[str, str]]:
    """Lit le compteur, avec refresh sur 401 et persistance immédiate des jetons.

    st/store sont les modules smartthings/state_store, passés par l'appelant
    pour éviter tout import en tête de module (sandbox).

    Retourne (kwh, watts, jetons_utilisés) ou lève la dernière erreur.
    """
    derniere_erreur: Exception | None = None
    for essai in range(NB_ESSAIS_LECTURE):
        try:
            kwh, watts = await st.lire_etat_compteur(
                http, tokens["access_token"], device_id
            )
            return kwh, watts, tokens
        except st.UnauthorisedError:
            # access token expiré : refresh + persistance IMMÉDIATE
            tokens = await st.rafraichir_jetons(
                http, creds["oauthClientId"], creds["oauthClientSecret"],
                tokens["refresh_token"],
            )
            tokens["obtained_at"] = _utcnow_str()
            await store.ecrire_document(
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


@workflows.activity(retry_policy_max_attempts=1)
async def lecture_deleguee(
    credentials: dict[str, Any],
    tokens: dict[str, Any],
    csv_lignes: list[str] | None = None,
    uploads: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mode délégué : lecture du compteur + téléversement vers URLs pré-signées.

    Aucun retry SDK (retry_policy_max_attempts=1) : un rejou relancerait la
    lecture avec des jetons d'entrée périmés si un refresh a eu lieu, ce qui
    casserait la chaîne du refresh token à usage unique. Les réessais réseau
    sont gérés dans la boucle interne ; en cas d'échec, les jetons courants
    (éventuellement rafraîchis) sont retournés pour persistance immédiate
    par l'appelant, et une ligne ERREUR est composée pour le CSV.

    uploads : {"csv": {url, method, headers}, "tokens": {url, method,
    headers}} — requêtes pré-signées de l'action « prepare » de l'API
    Libraries ; corps = octets bruts, pas de multipart, tout 2xx = succès.
    """
    import json

    import httpx

    from workflows import smartthings as st

    horodatage = _utcnow_str()
    maintenant = datetime.now(timezone.utc)
    device_id = credentials.get("deviceId") or credentials.get("energyMeterDeviceId")
    if not device_id:
        return {
            "statut": "erreur",
            "horodatage": horodatage,
            "erreur": "deviceId absent (credentials)",
            "jetons": tokens,
        }

    jetons_courants: dict[str, Any] = dict(tokens)
    kwh: str | None = None
    watts: str | None = None
    erreur: str | None = None
    rapport_uploads: dict[str, Any] = {}

    async with httpx.AsyncClient(base_url=st.ST_BASE, timeout=60.0) as http:
        derniere_erreur: Exception | None = None
        for essai in range(NB_ESSAIS_LECTURE):
            try:
                kwh, watts = await st.lire_etat_compteur(
                    http, jetons_courants["access_token"], device_id
                )
                derniere_erreur = None
                break
            except st.UnauthorisedError:
                try:
                    jetons_courants = await st.rafraichir_jetons(
                        http,
                        credentials["oauthClientId"],
                        credentials["oauthClientSecret"],
                        jetons_courants["refresh_token"],
                    )
                    jetons_courants["obtained_at"] = horodatage
                    print("Jetons SmartThings rafraîchis (mode délégué) — à persister par l'appelant.")
                    derniere_erreur = None
                except Exception as exc:
                    derniere_erreur = exc
                    break  # refresh en échec : ne pas rejouer avec un jeton mort
            except Exception as exc:  # transport, 5xx, réessai
                derniere_erreur = exc
                if essai < NB_ESSAIS_LECTURE - 1:
                    await asyncio.sleep(2 ** essai)

        if kwh is not None and watts is not None:
            ligne = f"{horodatage};{kwh};{watts}"
            statut = "ok"
            print(f"Relevé OK (mode délégué): {ligne}")
        else:
            motif = _motif(derniere_erreur) if derniere_erreur else "echec inconnu"
            ligne = f"{horodatage};ERREUR;{motif}"
            statut = "erreur"
            erreur = motif
            print(f"Relevé en ERREUR (mode délégué): {ligne}")

        # Persistance vers URLs pré-signées (corps bruts, pas de multipart).
        if uploads:
            lignes = list(csv_lignes) if csv_lignes else []
            if not lignes or not lignes[0].lower().startswith("horodatage"):
                lignes.insert(0, CSV_HEADER)
            if lignes[-1] != ligne:
                if statut == "erreur" or not _est_doublon_recent(
                    lignes, kwh or "", watts or "", maintenant
                ):
                    lignes.append(ligne)
            csv_contenu = ("\n".join(lignes) + "\n").encode()

            async def _televerser(requete: dict[str, Any], contenu: bytes) -> str:
                resp = await http.request(
                    requete.get("method", "PUT"),
                    requete["url"],
                    headers=requete.get("headers", {}),
                    content=contenu,
                )
                if 200 <= resp.status_code < 300:
                    return "televerse"
                return f"echec HTTP {resp.status_code}"

            req_csv = uploads.get("csv")
            if req_csv:
                try:
                    rapport_uploads["csv"] = await _televerser(req_csv, csv_contenu)
                except Exception as exc:
                    rapport_uploads["csv"] = f"echec: {_motif(exc)}"

            jetons_changes = jetons_courants != tokens
            req_tokens = uploads.get("tokens")
            if req_tokens and jetons_changes:
                try:
                    rapport_uploads["tokens"] = await _televerser(
                        req_tokens, json.dumps(jetons_courants, indent=2).encode()
                    )
                except Exception as exc:
                    rapport_uploads["tokens"] = f"echec: {_motif(exc)}"
            elif req_tokens:
                rapport_uploads["tokens"] = "inchanges"

    return {
        "statut": statut,
        "horodatage": horodatage,
        "kwh_cumules": kwh,
        "watts": watts,
        "erreur": erreur,
        "jetons": jetons_courants,
        "uploads_rapport": rapport_uploads,
    }


@workflows.activity(retry_policy_max_attempts=3, retry_policy_backoff_coefficient=2.0)
async def faire_le_releve() -> dict[str, Any]:
    """Activité complète (mode autonome) : chargement de l'état, lecture, persistance.

    Idempotente en cas de retry SDK : re-lit l'état depuis la library et ne
    réécrit pas une ligne déjà présente (garde anti-doublon).
    """
    # Imports non déterministes : uniquement dans le corps de l'activité,
    # jamais en tête de module (sandbox déterministe des workflows).
    import json
    import os

    import httpx

    from workflows import smartthings, state_store

    horodatage = _utcnow_str()
    maintenant = datetime.now(timezone.utc)
    library_name = os.environ.get("MAISON_LIBRARY_NAME", "maison-connectee")

    async with httpx.AsyncClient(base_url=state_store.MISTRAL_API, timeout=60.0) as http:
        lib_id = await state_store.trouver_ou_creer_library(http, library_name)

        creds_brut = await state_store.lire_texte(http, lib_id, CREDENTIALS_DOC)
        if not creds_brut:
            raise RuntimeError(
                f"Document {CREDENTIALS_DOC} introuvable dans la library {library_name}"
            )
        creds = json.loads(creds_brut)

        device_id = creds.get("deviceId") or creds.get("energyMeterDeviceId")
        if not device_id:
            device_id = os.environ.get("MAISON_ENERGY_DEVICE_ID")
        if not device_id:
            raise RuntimeError("deviceId absent (credentials ou MAISON_ENERGY_DEVICE_ID)")

        tokens_brut = await state_store.lire_texte(http, lib_id, TOKENS_DOC)
        if not tokens_brut:
            raise RuntimeError(
                f"Document {TOKENS_DOC} introuvable dans la library {library_name}"
            )
        tokens = json.loads(tokens_brut)

        csv_texte = await state_store.lire_texte(http, lib_id, CSV_DOC, defaut="")

        try:
            kwh, watts, _ = await _lecture(
                http, creds, tokens, lib_id, device_id, smartthings, state_store
            )
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
        if input.credentials is not None and input.tokens is not None:
            donnees = await lecture_deleguee(
                input.credentials, input.tokens, input.csv_lignes, input.uploads
            )
        else:
            donnees = await faire_le_releve()
        return ReleveResult(**donnees)
