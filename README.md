# How to run

## 1. Activate virtual environment

```
source venv/bin/activate
```

## 2. Install requirements in venv

```
pip install -r requirements.txt
```

## 3. Set up environment variables

Create a `.env` file inside `functions/` (next to `main.py`) with your local
values, e.g.:

```
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

- `.env` and `.env.local` are auto-loaded by the Firebase emulator — no
  `python-dotenv` needed.
- `.env.local` overrides `.env` and is never deployed; good place for a real
  key you don't want touching project config.
- Both files should be git-ignored (see `.gitignore`).

## 4. Run locally

- Set ADC to GCP project

```
gcloud auth application-default set-quota-project <PROJECT-ID>
```

```
firebase emulators:start --only functions
```

## 5. Deploy

```
firebase deploy --only functions
```

## 6. Manage secrets (production)

Production secrets are stored in Secret Manager, not `.env` — set them once
per environment:

```
firebase functions:secrets:set ANTHROPIC_API_KEY
```

- View a secret's value

```
firebase functions:secrets:access ANTHROPIC_API_KEY
```

- View a secret's metadata/versions (no value shown)

```
firebase functions:secrets:get ANTHROPIC_API_KEY
```

## 7. Bot Setup 
- Ensure Telegram can invoke your webhook

```
gcloud functions add-invoker-policy-binding main --region=us-central1 --member="allUsers"
```

> Note: there's no `firebase functions:secrets:list`. To see every secret in
> the project, use `gcloud secrets list` or check
> [Secret Manager in the Cloud Console](https://console.cloud.google.com/security/secret-manager).

Redeploy any function that references a secret after changing its value, or
it'll keep using the old one.

---

# Project structure

```
functions/
├── main.py                 # Firebase entry point only (Functions ↔ ASGI bridge)
├── requirements.txt
├── .env                    # local env vars (git-ignored)
├── .env.local               # local-only overrides (git-ignored)
└── app/
    ├── config.py             # env-based settings
    ├── firebase_app.py       # firebase_admin init + db.reference() wrapper
    ├── models.py              # dataclasses
    ├── fpl_client.py          # Fantasy Premier League API client
    ├── ai_schemas.py           # JSON schemas for Claude structured output
    ├── ai_client.py            # Claude call, prompt, hydration
    ├── squad_service.py        # Firebase-backed squad state + analysis flow
    ├── app_factory.py           # create_app() — FastAPI instance + CORS + routers
    └── routers/
        ├── players.py         # /api/bootstrap_static, /api/current_game_week, /api/player_ranking
        ├── squad.py            # /squad, /add_player, /remove_player, /clear_squad
        └── analysis.py         # /analyze
```
