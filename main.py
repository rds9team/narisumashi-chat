import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import traceback
from datetime import datetime

# python-dotenv が利用可能なら .env を読み込む（なければ環境変数 / 直書き fallback で動作）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 環境変数優先、取得できなければ直書きのデフォルト値で動作
TOKEN = os.environ.get("TOKEN", "token")
LOG_WEBHOOK_URL = os.environ.get("LOG_WEBHOOK_URL", "webhookURL")
WEBHOOK_ENABLED = os.environ.get("WEBHOOK_ENABLED", "false").lower() in ("true", "1")
LANG = os.environ.get("LANG", "ja").lower()

MESSAGES = {
    "ja": {
        "ready": "チャット偽装Bot 起動完了",
        "synced": "スラッシュコマンドを {n} 個同期しました",
        "sync_error": "コマンドの同期に失敗しました: {e}",
        "processing": "送信中...",
        "success": "送信しました",
        "error": "エラーが発生しました: {e}",
        "log_title": "ログ",
        "log_executor": "実行者",
        "log_target": "偽装ターゲット",
        "log_channel": "チャンネル",
        "log_message": "送信されたメッセージ",
        "log_username": "チャット偽装ログ",
    },
    "en": {
        "ready": "Impersonation chat bot is now running",
        "synced": "Synced {n} slash command(s)",
        "sync_error": "Failed to sync commands: {e}",
        "processing": "Sending...",
        "success": "Sent",
        "error": "An error occurred: {e}",
        "log_title": "Log",
        "log_executor": "Executor",
        "log_target": "Impersonation target",
        "log_channel": "Channel",
        "log_message": "Sent message",
        "log_username": "Impersonation chat log",
    },
}

msg = MESSAGES.get(LANG, MESSAGES["ja"])

# Botの初期設定（メンバー情報や表示名を正確に取得するためインテントを有効化）
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
member_cache_flags = discord.MemberCacheFlags.none()
max_messages = 10

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"====================================")
    print(f" {msg['ready']} ({bot.user.display_name})")
    print(f"====================================")

    try:
        # スラッシュコマンドをDiscord側に同期
        synced = await bot.tree.sync()
        print(f" [system] {msg['synced'].format(n=len(synced))}")
    except Exception as e:
        print(f" [error] {msg['sync_error'].format(e=e)}")


# スラッシュコマンド定義
@bot.tree.command(name="chat", description="Send a message impersonating the specified user.")
@app_commands.describe(user="User to impersonate (name autocomplete / direct ID)", message="Content to send")
async def chat(interaction: discord.Interaction, user: discord.User, message: str):

    # ephemeral=True にすることで、一般ユーザーの画面には痕跡を残しません
    await interaction.response.send_message(msg["processing"], ephemeral=True)

    channel = interaction.channel
    author = interaction.user

    try:
        # ターゲットのアバターURLを取得（設定されてなければNone）
        avatar_url = user.display_avatar.url if user.display_avatar else None

        # 1. チャンネルに一瞬だけ発言用のWebhookを作成
        webhook = await channel.create_webhook(name="System_Ghost")

        # 2. Webhook経由でターゲットの名前とアイコンを騙ってメッセージを送信
        await webhook.send(
            content=message,
            username=user.display_name,
            avatar_url=avatar_url
        )

        # 3. 送信が完了したら、即座にWebhookを削除
        await webhook.delete()

        # 4. コマンドを打った本人にだけ成功をこっそり報告
        await interaction.edit_original_response(content=msg["success"])

        # 5. ログ用Webhookへ詳細なリッチログ（Embed）を送信
        if WEBHOOK_ENABLED and LOG_WEBHOOK_URL:
            async with aiohttp.ClientSession() as session:
                log_webhook = discord.Webhook.from_url(LOG_WEBHOOK_URL, session=session)

                formatted_message = f"```\n{message}\n```"

                embed = discord.Embed(
                    title=msg["log_title"],
                    color=0x5865F2,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name=msg["log_executor"],
                    value=f"{author.mention}\n**display_name:** `{author.display_name}`\n**user_id:** `{author.id}`",
                    inline=False
                )
                embed.add_field(
                    name=msg["log_target"],
                    value=f"{user.mention}\n**display_name:** `{user.display_name}`\n**user_id:** `{user.id}`",
                    inline=False
                )
                embed.add_field(
                    name=msg["log_channel"],
                    value=f"{channel.mention}\n**channel_id:** `{channel.id}`",
                    inline=False
                )
                embed.add_field(
                    name=msg["log_message"],
                    value=formatted_message,
                    inline=False
                )
                embed.set_thumbnail(url=author.display_avatar.url if author.display_avatar else None)

                await log_webhook.send(embed=embed, username=msg["log_username"])

    except Exception as e:
        print(f"\n[error] /chat command failed.")
        print(f"--------------------------------------------------")
        traceback.print_exc()
        print(f"--------------------------------------------------\n")

        try:
            await interaction.edit_original_response(content=msg["error"].format(e=e))
        except:
            pass

# Botの起動
bot.run(TOKEN)
