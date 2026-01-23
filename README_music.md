# Music Bot (`musicBot.py`) 使い方

このドキュメントは、`musicBot.py` のセットアップ方法と使い方について説明します。

## 1. セットアップ

### 1-1. Discord Botの作成とトークンの取得

1.  [Discord Developer Portal](https://discord.com/developers/applications) にアクセスし、ログインします。
2.  右上の "New Application" をクリックし、Botの名前を入力して作成します。
3.  左側のメニューから "Bot" タブを選択します。
4.  "Add Bot" をクリックし、確認画面で "Yes, do it!" をクリックします。
5.  Botが作成されたら、"Token" セクションにある "Reset Token" をクリックします。
6.  表示されたトークンをコピーします。**このトークンは他人に教えないでください。**

### 1-2. Botの招待（重要）
スラッシュコマンドを使用するには、`applications.commands` スコープを含めてBotを招待する必要があります。

1.  Developer Portalの左メニューから **OAuth2** -> **URL Generator** をクリックします。
2.  **SCOPES** で `bot` と **`applications.commands`** にチェックを入れます。
3.  **BOT PERMISSIONS** で `Connect`, `Speak`, `View Channels`, `Send Messages` などを選択します。
4.  生成されたURLをコピーしてブラウザで開き、サーバーに招待します。
    *   **注意:** 既にBotがいる場合は、一度サーバーから追放（キック）してから、新しいURLで再招待してください。

### 1-3. 楽曲ファイルの準備
プロジェクトのルートディレクトリに `music` という名前のフォルダを作成します。
再生したいMP3ファイルをこの `music` フォルダの中に配置してください。

```
/discordBots
├── music/
│   ├── your_song_1.mp3
│   └── your_song_2.mp3
├── src/
│   └── musicBot.py
└── docker-compose.yml
```

`.gitignore` の設定により、`*.mp3` ファイルはGitの管理対象から除外されます。

### 1-4. 環境変数の設定
`.env.example` をコピーして `.env` ファイルを作成します。
`.env` ファイル内の `DISCORD_MUSIC_BOT_TOKEN` に、手順1-1で取得したBotトークンを設定してください。

```dotenv
# .env
DISCORD_MUSIC_BOT_TOKEN="ここにあなたのMusic Botのトークンを貼り付け"
# ... 他の設定
```

### 1-3. Botの起動
ターミナルで以下のコマンドを実行して、Botを起動します。

```bash
docker-compose up -d --build discord-music-bot
```
`--build` オプションは、初回起動時やコードを更新した際に必要です。

## 2. コマンドリファレンス

Music Botはスラッシュコマンド（`/`）を使用します。

### 接続・切断
- `/join_y`
  - コマンドを実行したユーザーがいるボイスチャンネルにBotが接続します。
- `/leave`
  - Botがボイスチャンネルから退出します。

### 再生コントロール
- `/play <ファイル名>`
  - `music` フォルダ内にある指定されたMP3ファイルを再生します。
  - 既に再生中の場合は、再生待ちリスト（キュー）に追加されます。
  - **例:** `/play filename:your_song_1.mp3`
- `/play_all`
  - `music` フォルダ内の全てのMP3ファイルをランダムな順番でキューに追加して再生します。
- `/nowplaying`
  - 現在再生中の曲名を表示します。
- `/queue`
  - 現在の再生待ちリスト（キュー）を表示します。
- `/pause` / `/resume`
  - 再生を一時停止／再開します。
- `/stop`
  - 再生を停止し、キューをクリアします。
- `/skip`
  - 現在再生中の曲をスキップして、キューにある次の曲を再生します。
- `/seek <秒数>`
  - 指定した秒数の位置から再生を開始します。(例: `/seek seconds:60`)
- `/forward [秒数]` / `/backward [秒数]`
  - 指定秒数だけ再生位置を進めたり戻したりします。秒数指定がない場合は10秒です。(例: `/forward seconds:30`)
- `/volume <音量>`
  - 音量を 0 から 100 の間の数値で設定します。(例: `/volume vol:50`)
- `/random`
  - `music` フォルダ内のMP3ファイルをランダムに1曲選び、キューに追加します。
- `/help`
  - 使用可能なコマンドの一覧と説明を表示します。