"""Worker Mistral Workflows — rappels Telegram.

Enregistre le workflow `rappel-telegram` et démarre le worker. Le déploiement
géré Mistral construit l'image depuis ce dépôt et le worker s'authentifie via
le token de service-account monté par la plateforme (MISTRAL_SA_TOKEN_PATH).
"""

import asyncio
import sys
from pathlib import Path

# /app/src sur sys.path pour importer le package `workflows` du projet.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mistralai.workflows as workflows  # noqa: E402

from workflows.rappel import RappelTelegramWorkflow  # noqa: E402


async def main() -> None:
    await workflows.run_worker([RappelTelegramWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
