# Rappels Telegram — Mistral Workflow

Workflow `rappel-telegram` qui envoie un message sur Telegram via l'API Bot
officielle (`POST https://api.telegram.org/bot<token>/sendMessage`).

Il est conçu pour être déclenché par des **schedules one-shot**
(`max_executions=1`, un calendar à la minute voulue), créés à la demande
depuis Vibe quand l'utilisateur demande un rappel (« rappelle-moi demain
9 h d'appeler le plombier » → le message arrive sur Telegram à 9 h).

## Architecture

- **Déploiement géré** : Mistral Cloud construit l'image depuis ce dépôt
  (déploiement `rappels-telegram`) et exécute le worker ; aucun secret dans
  le code ni dans l'image.
- **Identifiants** : deux secrets du workspace, liés au déploiement (onglet
  Settings de la console) :
  - secret `telegram_bot_token` (token du bot créé via @BotFather — jamais
    dans le code, jamais dans le chat), lu via l'env `TELEGRAM_BOT_TOKEN`
    (ou `telegram_bot_token`) ;
  - secret `telegram_chat_id` (chat ID de l'utilisateur, obtenu avec la
    commande `/id` du bot), lu via l'env `TELEGRAM_CHAT_ID` (ou
    `telegram_chat_id`). Peut aussi être passé explicitement dans l'input
    du workflow (`chat_id`).

## Entrée / sortie

```json
{"message": "Rappel : appeler le plombier", "chat_id": null}
```

Résultat : `{"statut": "ok", "message_id": 123}` ; en cas d'échec l'activité
lève une erreur et l'exécution apparaît en failed dans les traces.

## Création d'un rappel depuis Vibe

Voir la skill `rappel-telegram` : elle appelle
`mistral_mcp_create_workflow_schedule` avec
`workflow_identifier="rappel-telegram"`, `deployment_name="rappels-telegram"`
et un schedule one-shot (`calendars` à la date/heure demandées,
`time_zone_name="Europe/Paris"`, `max_executions=1`,
`input={"message": "..."}`).
