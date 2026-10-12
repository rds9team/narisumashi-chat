import os
import sys
import time
import asyncio
import traceback
from datetime import datetime
from typing import Optional

import aiohttp
from aiohttp import web
import discord
from discord import app_commands
from discord.ext import commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import database

# 環境変数
TOKEN = os.environ.get("DISCORD_TOKEN") or os.environ.get("TOKEN", "")
GLOBAL_LOG_WEBHOOK_URL = os.environ.get("GLOBAL_LOG_WEBHOOK_URL") or os.environ.get("LOG_WEBHOOK_URL", "")
API_PORT = int(os.environ.get("API_PORT", 8088))
DB_PATH = os.environ.get("DB_PATH", "settings.db")
LANG = os.environ.get("LANG", "ja").lower()

START_TIME = time.time()

# 多言語メッセージ定義
MESSAGES = {
    "ja": {
        "ready": "なりすましChat Bot 起動完了",
        "synced": "スラッシュコマンドを {n} 個同期しました",
        "sync_error": "コマンドの同期に失敗しました: {e}",
        "processing": "送信中...",
        "success": "送信しました",
        "error": "エラーが発生しました: {e}",
        "log_title": "なりすまし実行ログ",
        "log_executor": "実行者",
        "log_target": "偽装ターゲット",
        "log_channel": "チャンネル",
        "log_server": "サーバー",
        "log_message": "送信されたメッセージ",
        "log_username": "なりすまし監査ログ",
        "setting_title": "なりすましChat 設定",
        "setting_webhook_success": "ログ用Webhookを設定しました。テストメッセージを送信しました。",
        "setting_webhook_invalid": "無効なWebhook URLです。DiscordのWebhook URLを指定してください。",
        "setting_webhook_removed": "ログ用Webhookの設定を解除しました。",
        "setting_toggle_on": "ログ送信を有効にしました。",
        "setting_toggle_off": "ログ送信を無効にしました。",
        "setting_no_webhook": "ログ用Webhookが設定されていません。`/setting webhook` で登録してください。",
        "setting_test_success": "テストメッセージをWebhookに送信しました！",
        "setting_test_failed": "Webhookへの送信に失敗しました: {e}",
        "status_webhook": "Webhook URL",
        "status_log_enabled": "ログ送信状態",
        "status_configured": "設定済み",
        "status_not_configured": "未設定",
        "status_enabled": "有効 (ON)",
        "status_disabled": "無効 (OFF)",
    },
    "en": {
        "ready": "Impersonation Chat Bot is now running",
        "synced": "Synced {n} slash command(s)",
        "sync_error": "Failed to sync commands: {e}",
        "processing": "Sending...",
        "success": "Sent",
        "error": "An error occurred: {e}",
        "log_title": "Impersonation Audit Log",
        "log_executor": "Executor",
        "log_target": "Impersonation Target",
        "log_channel": "Channel",
        "log_server": "Server",
        "log_message": "Message Content",
        "log_username": "Impersonation Audit",
        "setting_title": "Impersonation Chat Settings",
        "setting_webhook_success": "Log webhook has been updated. A test message was sent.",
        "setting_webhook_invalid": "Invalid webhook URL. Please provide a valid Discord webhook URL.",
        "setting_webhook_removed": "Log webhook setting has been removed.",
        "setting_toggle_on": "Logging has been enabled.",
        "setting_toggle_off": "Logging has been disabled.",
        "setting_no_webhook": "No log webhook configured. Use `/setting webhook` to register one.",
        "setting_test_success": "Test message sent successfully!",
        "setting_test_failed": "Failed to send test message: {e}",
        "status_webhook": "Webhook URL",
        "status_log_enabled": "Logging Status",
        "status_configured": "Configured",
        "status_not_configured": "Not configured",
        "status_enabled": "Enabled (ON)",
        "status_disabled": "Disabled (OFF)",
    },
}

msg = MESSAGES.get(LANG, MESSAGES["ja"])

# Discord Bot 初期化
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True


class ImpersonationBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.session: Optional[aiohttp.ClientSession] = None
        self.web_runner: Optional[web.AppRunner] = None

    async def setup_hook(self):
        # データベース初期化
        database.init_db(DB_PATH)
        self.session = aiohttp.ClientSession()

        # Web APIサーバーの起動
        await self.start_web_server()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        if self.web_runner:
            await self.web_runner.cleanup()
        await super().close()

    async def start_web_server(self):
        app = web.Application()

        async def root_handler(request: web.Request):
            return web.json_response({
                "service": "narisumashi-chat",
                "version": "v2.0",
                "status": "online",
                "endpoints": [
                    {"path": "/health", "method": "GET"},
                    {"path": "/stats", "method": "GET"},
                ],
            })

        async def health_handler(request: web.Request):
            return web.json_response({
                "status": "ok",
                "service": "narisumashi-chat",
                "uptime_seconds": int(time.time() - START_TIME),
                "timestamp": datetime.now().isoformat(),
            })

        async def stats_handler(request: web.Request):
            guild_count = len(self.guilds)
            user_count = sum(g.member_count or 0 for g in self.guilds)
            latency = round(self.latency * 1000, 1) if self.latency else 0.0
            return web.json_response({
                "status": "online",
                "bot_name": "なりすましchat",
                "bot_id": str(self.user.id) if self.user else "",
                "guilds": guild_count,
                "users": user_count,
                "ping": latency,
                "uptime_seconds": int(time.time() - START_TIME),
                "version": "v2.0",
            })

        # CORS対応
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        async def cors_middleware(app, handler):
            async def middleware_handler(request):
                if request.method == "OPTIONS":
                    return web.Response(status=204, headers=cors_headers)
                response = await handler(request)
                response.headers.update(cors_headers)
                return response
            return middleware_handler

        app.middlewares.append(cors_middleware)
        app.router.add_get("/", root_handler)
        app.router.add_get("/health", health_handler)
        app.router.add_get("/api/health", health_handler)
        app.router.add_get("/stats", stats_handler)
        app.router.add_get("/api/stats", stats_handler)

        self.web_runner = web.AppRunner(app)
        await self.web_runner.setup()
        site = web.TCPSite(self.web_runner, "0.0.0.0", API_PORT)
        try:
            await site.start()
            print(f"[API] Web API server running on port {API_PORT}")
        except Exception as e:
            print(f"[API Error] Failed to bind Web API on port {API_PORT}: {e}")


bot = ImpersonationBot()


@bot.event
async def on_ready():
    print("====================================")
    print(f" {msg['ready']} ({bot.user.name}#{bot.user.discriminator})")
    print("====================================")

    try:
        synced = await bot.tree.sync()
        print(f"[system] {msg['synced'].format(n=len(synced))}")
    except Exception as e:
        print(f"[error] {msg['sync_error'].format(e=e)}")


# 監査ログ送信ヘルパー
async def send_audit_log(
    webhook_url: str,
    author: discord.User | discord.Member,
    target: discord.User,
    channel: discord.abc.GuildChannel,
    guild: Optional[discord.Guild],
    message: str,
):
    try:
        async with aiohttp.ClientSession() as session:
            log_webhook = discord.Webhook.from_url(webhook_url, session=session)
            embed = discord.Embed(
                title=msg["log_title"],
                color=0x5865F2,
                timestamp=datetime.now(),
            )
            embed.add_field(
                name=msg["log_executor"],
                value=f"{author.mention}\n**display_name:** `{author.display_name}`\n**user_id:** `{author.id}`",
                inline=True,
            )
            embed.add_field(
                name=msg["log_target"],
                value=f"{target.mention}\n**display_name:** `{target.display_name}`\n**user_id:** `{target.id}`",
                inline=True,
            )
            channel_info = f"{channel.mention}\n**channel_id:** `{channel.id}`"
            embed.add_field(name=msg["log_channel"], value=channel_info, inline=False)

            if guild:
                guild_info = f"**{guild.name}** (`{guild.id}`)"
                embed.add_field(name=msg["log_server"], value=guild_info, inline=False)

            embed.add_field(
                name=msg["log_message"],
                value=f"```\n{message}\n```",
                inline=False,
            )
            avatar_url = author.display_avatar.url if author.display_avatar else None
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

            await log_webhook.send(embed=embed, username=msg["log_username"])
    except Exception as e:
        print(f"[Audit Log Error] Failed to send audit log to {webhook_url}: {e}")


# ==========================================
# /chat コマンド
# ==========================================
@bot.tree.command(name="chat", description="指定したユーザーになりすましてメッセージを送信します")
@app_commands.describe(user="なりすまし対象のユーザー", message="送信するメッセージ内容")
async def chat_cmd(interaction: discord.Interaction, user: discord.User, message: str):
    await interaction.response.send_message(msg["processing"], ephemeral=True)

    channel = interaction.channel
    author = interaction.user
    guild = interaction.guild

    try:
        avatar_url = user.display_avatar.url if user.display_avatar else None

        # 1. 一時的な Webhook を作成
        webhook = await channel.create_webhook(name="System_Ghost")

        # 2. メッセージを送信
        await webhook.send(
            content=message,
            username=user.display_name,
            avatar_url=avatar_url,
        )

        # 3. Webhook を削除
        await webhook.delete()

        # 4. 実行者に報告
        await interaction.edit_original_response(content=msg["success"])

        # 5. ギルド個別のログ送信用 Webhook へ送信
        if guild:
            setting = database.get_guild_setting(guild.id, DB_PATH)
            if setting and setting.get("log_webhook_url") and setting.get("log_enabled"):
                await send_audit_log(
                    webhook_url=setting["log_webhook_url"],
                    author=author,
                    target=user,
                    channel=channel,
                    guild=guild,
                    message=message,
                )

        # 6. グローバル管理者用ログ Webhook へ送信 (設定されている場合)
        if GLOBAL_LOG_WEBHOOK_URL:
            await send_audit_log(
                webhook_url=GLOBAL_LOG_WEBHOOK_URL,
                author=author,
                target=user,
                channel=channel,
                guild=guild,
                message=message,
            )

    except Exception as e:
        print(f"\n[error] /chat command failed: {e}")
        traceback.print_exc()
        try:
            await interaction.edit_original_response(content=msg["error"].format(e=e))
        except Exception:
            pass


# ==========================================
# /setting コマンドグループ
# ==========================================
@app_commands.default_permissions(manage_guild=True)
@app_commands.guild_only()
class SettingGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="setting",
            description="サーバーごとのなりすましBot設定（管理者専用）",
        )

    @app_commands.command(name="webhook", description="誰がなりすましを実行したかのログ受信用 Webhook URL を設定します")
    @app_commands.describe(url="DiscordのWebhook URL")
    async def set_webhook(self, interaction: discord.Interaction, url: str):
        guild = interaction.guild
        if not guild:
            return

        if not url.startswith("https://discord.com/api/webhooks/") and not url.startswith("https://discordapp.com/api/webhooks/"):
            await interaction.response.send_message(msg["setting_webhook_invalid"], ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # 疎通確認テスト送信
        try:
            async with aiohttp.ClientSession() as session:
                wh = discord.Webhook.from_url(url, session=session)
                embed = discord.Embed(
                    title=msg["setting_title"],
                    description=f"{interaction.user.mention} がこのWebhookを監査ログ通知先に設定しました。",
                    color=0x2ecc71,
                    timestamp=datetime.now(),
                )
                await wh.send(embed=embed, username=msg["log_username"])
        except Exception as e:
            await interaction.followup.send(msg["setting_test_failed"].format(e=e), ephemeral=True)
            return

        # DBに保存
        database.set_guild_webhook(guild.id, url, DB_PATH)
        await interaction.followup.send(msg["setting_webhook_success"], ephemeral=True)

    @app_commands.command(name="status", description="現在のサーバー設定を確認します")
    async def status(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        setting = database.get_guild_setting(guild.id, DB_PATH)
        has_wh = bool(setting and setting.get("log_webhook_url"))
        enabled = bool(setting and setting.get("log_enabled")) if has_wh else False

        embed = discord.Embed(
            title=f"{guild.name} - {msg['setting_title']}",
            color=0x5865F2,
            timestamp=datetime.now(),
        )
        embed.add_field(
            name=msg["status_webhook"],
            value=f"✅ {msg['status_configured']}" if has_wh else f"❌ {msg['status_not_configured']}",
            inline=True,
        )
        embed.add_field(
            name=msg["status_log_enabled"],
            value=f"🟢 {msg['status_enabled']}" if enabled else f"🔴 {msg['status_disabled']}",
            inline=True,
        )
        if setting and setting.get("updated_at"):
            embed.add_field(name="最終更新", value=f"`{setting['updated_at']}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remove_webhook", description="登録されているログ用 Webhook を解除します")
    async def remove_webhook(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        database.remove_guild_webhook(guild.id, DB_PATH)
        await interaction.response.send_message(msg["setting_webhook_removed"], ephemeral=True)

    @app_commands.command(name="toggle_log", description="ログ送信の有効/無効を切り替えます")
    async def toggle_log(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        setting = database.get_guild_setting(guild.id, DB_PATH)
        current = bool(setting and setting.get("log_enabled"))
        new_val = not current
        database.set_guild_log_enabled(guild.id, new_val, DB_PATH)

        response_msg = msg["setting_toggle_on"] if new_val else msg["setting_toggle_off"]
        await interaction.response.send_message(response_msg, ephemeral=True)

    @app_commands.command(name="test", description="設定されている Webhook へテスト通知を送信します")
    async def test(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        setting = database.get_guild_setting(guild.id, DB_PATH)
        if not setting or not setting.get("log_webhook_url"):
            await interaction.response.send_message(msg["setting_no_webhook"], ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                wh = discord.Webhook.from_url(setting["log_webhook_url"], session=session)
                embed = discord.Embed(
                    title=f"[テスト] {msg['log_title']}",
                    description=f"{interaction.user.mention} がWebhookのテスト送信を実行しました。正常に受信できています。",
                    color=0x2ecc71,
                    timestamp=datetime.now(),
                )
                await wh.send(embed=embed, username=msg["log_username"])
            await interaction.followup.send(msg["setting_test_success"], ephemeral=True)
        except Exception as e:
            await interaction.followup.send(msg["setting_test_failed"].format(e=e), ephemeral=True)


bot.tree.add_command(SettingGroup())


def main():
    if not TOKEN:
        print("[Error] Discord Token is not specified in environment variable (DISCORD_TOKEN or TOKEN).")
        print("Please configure .env file or environment variables before running.")
        sys.exit(1)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
