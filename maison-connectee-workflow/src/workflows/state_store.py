"""Stockage durable via l'API Mistral Libraries (REST, sans SDK).

Le contenu du worker est sans état : l'état du workflow (jetons SmartThings,
CSV des relevés) vit dans une library Mistral, via l'API REST :
- GET    /v1/libraries
- POST   /v1/libraries
- GET    /v1/libraries/{id}/documents
- POST   /v1/libraries/{id}/documents        (multipart, champ "file")
- DELETE /v1/libraries/{id}/documents/{doc_id}
- GET    /v1/libraries/{id}/documents/{doc_id}/signed-url   -> URL du contenu brut

Authentification : l'API Libraries exige une identité Mistral (« User id is
required ») que le token Kubernetes du service account ne porte pas. On
utilise donc la clé API liée au déploiement depuis le Secrets Manager du
workspace (variable d'environnement MAISON_API_KEY), avec repli sur le token
du service account (MISTRAL_SA_TOKEN_PATH).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

MISTRAL_API = "https://api.mistral.ai"


def _credential() -> str:
    """Clé API depuis le secret lié au déploiement, sinon token du service account."""
    cle = os.environ.get("MAISON_API_KEY")
    if cle:
        return cle.strip()
    path = os.environ.get("MISTRAL_SA_TOKEN_PATH")
    if not path:
        raise RuntimeError("MAISON_API_KEY absent et MISTRAL_SA_TOKEN_PATH absent")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_credential()}"}


async def trouver_ou_creer_library(http: httpx.AsyncClient, nom: str) -> str:
    """Retourne l'id de la library nommée ``nom``, la crée (partagage workspace) sinon."""
    resp = await http.get("/v1/libraries", headers=_headers(), params={"search": nom})
    if resp.status_code == 401:
        print(f"401 sur /v1/libraries (credential utilise: "
              f"{'MAISON_API_KEY' if os.environ.get('MAISON_API_KEY') else 'SA token'}): "
              f"{resp.text[:200]}")
    resp.raise_for_status()
    for lib in resp.json().get("data", []):
        if lib.get("name") == nom:
            return str(lib["id"])
    resp = await http.post(
        "/v1/libraries",
        headers=_headers(),
        json={"name": nom, "owner_type": "Workspace"},
    )
    resp.raise_for_status()
    return str(resp.json()["id"])


async def lister_documents(
    http: httpx.AsyncClient, library_id: str, nom: str
) -> list[dict[str, Any]]:
    """Documents de la library portant exactement ce nom, du plus récent au plus ancien."""
    resp = await http.get(
        f"/v1/libraries/{library_id}/documents",
        headers=_headers(),
        params={"page_size": 100},
    )
    resp.raise_for_status()
    docs = [d for d in resp.json().get("data", []) if d.get("name") == nom]
    docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return docs


async def lire_document(
    http: httpx.AsyncClient, library_id: str, document_id: str
) -> str:
    """Contenu brut d'un document (via signed-url, la réponse est une chaîne JSON)."""
    resp = await http.get(
        f"/v1/libraries/{library_id}/documents/{document_id}/signed-url",
        headers=_headers(),
    )
    resp.raise_for_status()
    data: Any = resp.json()
    if isinstance(data, str):
        url = data
    elif isinstance(data, dict):
        url = data.get("url") or data.get("signed_url")
    else:
        raise RuntimeError(f"signed-url inattendu: {data!r}")
    if not url:
        raise RuntimeError(f"signed-url vide: {data!r}")
    raw = await http.get(url)  # URL absolue : httpx ignore base_url
    raw.raise_for_status()
    return raw.text


async def ecrire_document(
    http: httpx.AsyncClient, library_id: str, nom: str, contenu: bytes
) -> None:
    """Remplace le document ``nom`` : téléverse la nouvelle version puis supprime les anciennes.

    Téléverser avant de supprimer évite toute fenêtre de perte de données ;
    les doublons momentanés sont tolérés et nettoyés au prochain passage.
    """
    anciens = await lister_documents(http, library_id, nom)
    resp = await http.post(
        f"/v1/libraries/{library_id}/documents",
        headers=_headers(),
        files={"file": (nom, contenu, "application/octet-stream")},
    )
    resp.raise_for_status()
    for doc in anciens:
        try:
            await http.delete(
                f"/v1/libraries/{library_id}/documents/{doc['id']}",
                headers=_headers(),
            )
        except httpx.HTTPError:
            # doublon momentané, nettoyé au prochain passage
            pass


async def lire_texte(
    http: httpx.AsyncClient, library_id: str, nom: str, defaut: str | None = None
) -> str | None:
    """Lit le document le plus récent nommé ``nom`` ; ``defaut`` s'il n'existe pas."""
    docs = await lister_documents(http, library_id, nom)
    if not docs:
        return defaut
    return await lire_document(http, library_id, str(docs[0]["id"]))


def maintenant_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
