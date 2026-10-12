# なりすましchat (Impersonation Chat Bot)

Discord 上で、指定したユーザーの名前とアイコンを騙ってメッセージを送信する Bot です。
送信には一時的な Webhook を使用し、送信後に即座に削除するため痕跡を残しません。

また、各サーバーの管理者が「誰がいつなりすましを実行したか」を把握できるように、サーバー個別の監査ログ用 Webhook を設定する機能を備えています。

> 注意: この Bot は他者のなりすましを行う機能です。利用は必ず相手の同意がある場面・遊びの範囲で、各サーバーのルールおよび Discord の利用規約を遵守して行ってください。

## 機能

- `/chat` コマンドで任意のユーザーになりすまして発言
- コマンド実行者には `ephemeral` メッセージのみ表示され、一般ユーザーの画面には痕跡が残らない
- **サーバー個別ログ機能**: 各サーバー管理者が `/setting webhook` で自サーバー用の監査ログ Webhook を設定可能
- 実行時に誰が誰になりすましたかの詳細ログ（Embed）を自動送信
- **内部 Web API**: VPS / API Gateway と連携可能な `/health`, `/stats` エンドポイントを搭載
- メッセージの言語は `ja` / `en` を切り替え可能

## コマンド一覧

### 一般コマンド
- `/chat user:<ユーザー> message:<内容>`
  - `user`: なりすまし対象のユーザー（名前入力で予測 / ID 直接も可）
  - `message`: 送信する内容

### 管理者設定コマンド (`/setting` グループ - サーバー管理権限が必要)
- `/setting webhook url:<Webhook URL>`: サーバー専用の監査ログ送信用 Webhook を設定（自動疎通テスト付き）
- `/setting status`: 現在のサーバーのログ設定状態を確認
- `/setting remove_webhook`: 設定されているログ用 Webhook を解除
- `/setting toggle_log`: ログ送信の有効 / 無効を切り替え
- `/setting test`: 設定されている Webhook へテスト通知を送信

## セットアップ

1. 依存関係をインストール

   ```bash
   pip install -r requirements.txt
   ```

2. `.env` を作成（`.env.example` をコピーして編集）

   ```bash
   cp .env.example .env
   ```

   | 変数 | 説明 | デフォルト |
   | --- | --- | --- |
   | `DISCORD_TOKEN` | Discord Bot のトークン（必須） | - |
   | `GLOBAL_LOG_WEBHOOK_URL` | 全体管理者向けログ送信用 Webhook URL（任意） | 空 |
   | `API_PORT` | 内部 Web API ポート | `8088` |
   | `DB_PATH` | 設定保存用 SQLite DB パス | `settings.db` |
   | `LANG` | メッセージ言語（`ja` / `en`） | `ja` |

3. Bot を起動

   ```bash
   python main.py
   ```

   PM2 での起動例:
   ```bash
   pm2 start ecosystem.config.js
   ```

## 内部 Web API

API ポート（デフォルト: `8088`）にて以下のエンドポイントが提供されます。

- `GET /health` (`/api/health`): ヘルスチェック
- `GET /stats` (`/api/stats`): Botステータス（参加サーバー数、ユーザー数、Ping、稼働時間など）

## Bot 権限

Discord Developer Portal で以下のインテントを有効にしてください。

- Server Members Intent
- Message Content Intent

また、コマンドを実行するチャンネルで「Webhook の管理」権限が必要です。

## もしバグなどがあれば

Discordで @rds9 に連絡するかIssueを書いてください。

## 公開ホスト版（自分で動かさず使う）

作者がホストしている公開 Bot を用意しています。以下のリンクからサーバーに追加するだけで使えます（自分でトークンを用意したりサーバーを建てる必要はありません）。

https://discord.com/oauth2/authorize?client_id=1516341048639488061

## ライセンス

MIT — 詳細は `LICENSE` を参照してください。
