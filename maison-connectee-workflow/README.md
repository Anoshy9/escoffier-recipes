# Maison connectée — Relevé d'énergie (Mistral Workflow)

Workflow Mistral qui relève chaque jour le compteur d'énergie de la maison
d'Auvers-sur-Oise via l'app SmartThings « Vibe » (OAuth, lecture seule) et
ajoute une ligne au CSV `releves-energie.csv`. **Silencieux** : aucune
notification en cas de succès ; une ligne `ERREUR` est consignée en cas
d'échec.

## Architecture

- **Déploiement géré** : Mistral Cloud construit l'image depuis ce dépôt et
  exécute le worker (authentification par service-account, aucun secret
  dans le code).
- **État durable** : le contenu du worker est sans état. Jetons SmartThings et
  CSV vivent dans une library Mistral « maison-connectee » (documents
  `smartthings-credentials.json`, `smartthings-tokens.json`,
  `releves-energie.csv`), via l'API REST Libraries.
- **Chaîne de jetons** : access token 24 h ; refresh token 30 jours, renouvelé
  à chaque usage (usage unique). Après chaque refresh, le workflow
  **persiste immédiatement** les nouveaux jetons, sans quoi la chaîne casse.

## Format CSV

```
horodatage;kwh_cumules;watts
2026-10-27T12:17:02Z;9286.933;268.024
2026-10-28T08:00:00Z;ERREUR;<motif court>
```

Horodatage UTC ISO 8601 (Z), valeurs brutes sans unité.

## Réparation manuelle (chaîne cassée)

1. Si le refresh token meurt (`invalid_grant`) : régénérer le couple
   client/secret sur le portail développeur SmartThings
   (POST /v1/apps/{appId}/oauth/generate **avec** body clientName/scope/
   redirectUris/grantTypes), puis reprendre le flux d'autorisation
   (code via l'URL d'autorisation + échange) et mettre à jour
   `smartthings-tokens.json` et `smartthings-credentials.json` dans la
   library.
2. Le document le plus récent fait foi (les doublons
   momentanés sont nettoyés au passage suivant).

## Variables d'environnement (toutes optionnelles)

- `MAISON_LIBRARY_NAME` (défaut `maison-connectee`)
- `MAISON_ENERGY_DEVICE_ID` (défaut : le compteur d'énergie d'Auvers-sur-Oise)
