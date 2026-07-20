# なりすましchat (Impersonation Chat Bot)

Discord 上で、指定したユーザーの名前とアイコンを騙ってメッセージを送信する Bot です。
送信には一時的な Webhook を使用し、送信後に即座に削除するため痕跡を残しません。

> 注意: この Bot は他者のなりすましを行う機能です。利用は必ず相手の同意がある場面・遊びの範囲で、各サーバーのルールおよび Discord の利用規約を遵守して行ってください。

## 機能

- `/chat` コマンドで任意のユーザーになりすまして発言
- コマンド実行者には `ephemeral` メッセージのみ表示され、一般ユーザーの画面には痕跡が残らない
- オプションでログ用 Webhook へ実行内容を Embed で送信可能
- メッセージの言語は `ja` / `en` を切り替え可能

## セットアップ

1. 依存をインストール

   ```bash
   pip install -r requirements.txt
   ```

2. `.env` を作成（`.env.example` をコピーして編集）

   ```bash
   cp .env.example .env
   ```

   | 変数 | 説明 |
   | --- | --- |
   | `TOKEN` | Discord Bot のトークン（必須） |
   | `LOG_WEBHOOK_URL` | ログ送信用 Webhook URL（省略可） |
   | `WEBHOOK_ENABLED` | ログ送信の ON/OFF（`true` / `false`） |
   | `LANG` | メッセージ言語（`ja` / `en`） |

   `.env` がなくても `os.environ` から読み込みます。どちらも無い場合はソース内のデフォルト値で動作します（トークンは自分で設定してください）。

3. Bot を起動

   ```bash
   python main.py
   ```

## コマンド

- `/chat user:<ユーザー> message:<内容>`
  - `user`: なりすまし対象のユーザー（名前入力で予測 / ID 直接も可）
  - `message`: 送信する内容

## Bot 権限

以下のインテントを有効にしてください（Discord Developer Portal）。

- Server Members Intent
- Message Content Intent

また、コマンドを実行するチャンネルで「Webhook の管理」権限が必要です。

## 公開ホスト版（自分で動かさず使う）

作者がホストしている公開 Bot を用意しています。以下のリンクからサーバーに追加するだけで使えます（自分でトークンを用意したりサーバーを建てる必要はありません）。

https://discord.com/oauth2/authorize?client_id=1516341048639488061

## ライセンス

MIT — 詳細は `LICENSE` を参照してください。
