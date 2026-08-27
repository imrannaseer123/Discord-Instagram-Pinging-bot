
# Discord Insta ping bot

![python](https://img.shields.io/badge/python-3.8%2B-blue) ![status](https://img.shields.io/badge/status-active-success)

Discord Insta ping bot is a focused, easy-to-run Python utility that automates Instagram session handling and subscription tracking. It's designed for self-hosted deployments and lightweight hosting platforms (Railway, Heroku, etc.).

---

## Table of Contents

- [Why Discord Insta ping bot](#why-discord-insta-ping-bot)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Discord Commands](#discord-commands)
- [Usage Examples](#usage-examples)
- [Deployment](#deployment)
- [Security](#security)
- [Files](#files)
- [Contributing](#contributing)
- [License](#license)

---

## Why Discord Insta ping bot

If you need a minimal, maintainable bot to persist Instagram sessions, manage subscriptions, and run periodic tasks without a heavy framework, Discord Insta ping bot provides a small, auditable codebase to get started quickly.

## Features

- Persistent session management (`ig_sessions.json`).
- Subscription/notification storage using SQLite (`insta_subscriptions.db`).
- Environment-driven configuration via `.env` (kept out of source control).
- Ready for simple deployments (`Procfile`, `railway.json`).

## Quick Start

1. Clone the project:

```bash
git clone <repo-url>
cd dcbotinsta
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Create your `.env` from the example and edit it:

```bash
copy .env.example .env
```

Open `.env` and set your values. Example variables:

```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
SESSION_FILE=ig_sessions.json
DATABASE=insta_subscriptions.db
```

5. Run the bot:

```bash
python dcinstabot.py
```

## Configuration

- Use `.env` to provide secrets and configuration. Keep `.env` local and never commit it.
- The example `.env.example` contains placeholders and should be safe to commit.

## Discord Commands

The bot registers these Discord slash commands. Type `/` in a server where the bot is installed to see them and their arguments.

| Command | Arguments | Purpose |
| --- | --- | --- |
| `/insta_last` | `username`, `amount` | Fetch the latest posts from a public Instagram account. |
| `/insta_search` | `query`, `amount` | Search recent posts for a hashtag or keyword. The `#` prefix is optional. |
| `/insta_sub` | `username` | Subscribe the current channel to an Instagram account. New posts and reels are posted automatically. |
| `/insta_unsub` | `username` | Remove an Instagram subscription from the current server. |
| `/insta_list` | None | List the Instagram accounts currently subscribed in the server. |

### Command Examples

Fetch the five latest posts from an account:

```text
/insta_last username:nasa amount:5
```

Search for three recent posts using a hashtag:

```text
/insta_search query:#python amount:3
```

Start and stop automatic notifications:

```text
/insta_sub username:nasa
/insta_unsub username:nasa
```

View all current subscriptions:

```text
/insta_list
```

Subscriptions are checked once per day. The bot only fetches public Instagram accounts, and notifications are sent to the channel selected when `/insta_sub` is used.

## Usage Examples

- Start locally for testing:

```bash
python dcinstabot.py --verbose
```

- Run in the background (Linux/macOS):

```bash
nohup python dcinstabot.py &
```

## Deployment

- For Railway/Heroku-like platforms, `Procfile` is included. Ensure environment variables are set in the platform UI rather than committing `.env`.

## Security

- `.env` is listed in `.gitignore` to avoid accidental commits. Confirm before pushing.
- If secrets were committed, rotate them immediately.
- To remove `.env` from the repo index (safe):

```bash
git rm --cached .env
git commit -m "Remove .env from repository"
git push
```

- To purge `.env` from history (destructive): use BFG or `git filter-branch`; follow repository backup best practices before rewriting history.

## Important Files

- `dcinstabot.py` — main entrypoint and orchestration.
- `ig_sessions.json` — session store (do not commit live sessions).
- `insta_subscriptions.db` — SQLite DB for subscriptions.
- `.env.example` — example config; safe to commit.
- `.env` — local secrets (gitignored).

## Contributing

Contributions and issues are welcome. Please:

1. Fork the repo.
2. Create a feature branch.
3. Open a PR with a clear description and tests or manual validation steps.

## License

No license file is included. Add a `LICENSE` (e.g., MIT) to clarify reuse terms.

---

If you'd like, I can also: add a `LICENSE`, create a polished `.env.example`, or commit these changes for you.


