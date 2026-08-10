# Impersonation Chat Bot

A Discord bot that allows you to send messages using the **name and avatar of a specified user**.

The bot uses a temporary Webhook to send the message and immediately deletes the Webhook after sending.

> ⚠️ **Important:** This bot is designed for impersonation. Only use it with the target user's consent and for harmless entertainment. Always follow the rules of the Discord server and Discord's Terms of Service.

## Features

- Send a message while impersonating any selected user with the `/chat` command
- Select the target user by name with autocomplete, or specify their ID directly
- The command response is sent as an ephemeral message and is only visible to the command executor
- Optionally send execution logs to a logging Webhook as an Embed
- Supports both Japanese (`ja`) and English (`en`)
- Temporary Webhooks are deleted immediately after use

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a `.env` file

Copy `.env.example` to `.env` and edit the values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `TOKEN` | Discord Bot token (**required**) |
| `LOG_WEBHOOK_URL` | Webhook URL used for execution logs (optional) |
| `WEBHOOK_ENABLED` | Enable or disable logging (`true` / `false`) |
| `LANG` | Message language (`ja` / `en`) |

The bot can also read these values from environment variables without a `.env` file.

If a value is not provided through either method, the source code's default value will be used.

> The Bot token must always be provided by you.

### 3. Start the bot

```bash
python main.py
```

## Commands

### `/chat`

```text
/chat user:<user> message:<message>
```

**Arguments:**

- `user`: The user to impersonate. You can select a user by name using autocomplete or enter their ID directly.
- `message`: The message to send.

## Bot Permissions

The following intents must be enabled in the **Discord Developer Portal**:

- Server Members Intent
- Message Content Intent

Additionally, the bot requires the **Manage Webhooks** permission in the channel where the command is executed.

## Public Hosted Version

Don't want to host the bot yourself?

A publicly hosted version is available. You can simply add it to your Discord server without setting up a bot token or hosting environment yourself.

https://discord.com/oauth2/authorize?client_id=1516341048639488061

## Issues & Contact

If you find a bug or have a suggestion, please contact **@rds9 on Discord** or open an Issue on this repository.

## License

MIT — see [LICENSE](LICENSE) for details.