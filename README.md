# Discord Bots Collection (TTS & Music)

このリポジトリは、**VOICEVOXを使用した日本語読み上げBot (TTS Bot)** と、**ローカルのMP3ファイルを再生する音楽Bot (Music Bot)** の2つのDiscord Botを含んでいます。
DockerおよびDocker Composeを使用して、両方のBotとVOICEVOXエンジンを簡単に一括管理・起動できます。

## 機能概要

### 🗣️ TTS Bot (読み上げBot)
*   **VOICEVOX連携**: VOICEVOXエンジン（デフォルトはずんだもん）を使用して、高品質な日本語読み上げを行います。
*   **リアルタイム読み上げ**: ボイスチャンネル参加中に、特定のテキストチャンネルのメッセージを読み上げます。
*   **自動挨拶**: 参加時に「シフトはいりまーす」、退出時に「サラダバー」と挨拶します。
*   **キューシステム**: メッセージを順番に読み上げます。

### 🎵 Music Bot (音楽Bot)
*   **ローカル再生**: `music/` フォルダに配置されたMP3ファイルを再生します。
*   **キュー管理**: `/play` コマンドやランダム再生で、曲を再生待ちリストに追加・管理します。
*   **再生コントロール**: 再生、一時停止、再開、停止、スキップ、シーク、早送り、巻き戻しなどの操作が可能です。
*   **ランダム・全曲再生**: ランダムに1曲選んで再生したり、フォルダ内の全曲をシャッフルして再生したりできます。
*   **音量調整**: 再生音量を調整できます。

## 必要要件

*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/)

## セットアップ手順

### 1. Discord Botの作成

TTS Bot用とMusic Bot用で、それぞれ（または1つのBotで機能を兼ねる場合は1つ）Botアカウントを作成する必要があります。[Discord Developer Portal](https://discord.com/developers/applications) で設定を行ってください。

1.  **New Application** でアプリを作成。
2.  **Bot** タブで "Add Bot" をクリック。
3.  **Privileged Gateway Intents** セクションの **Message Content Intent** を**有効 (ON)** にする（読み上げやコマンド認識に必須）。
4.  **Token** をリセットしてコピーしておく。
5.  **OAuth2** -> **URL Generator** で招待URLを作成：
    *   **Scopes**: `bot`, `applications.commands`
    *   **Bot Permissions**:
        *   General: `View Channels`, `Send Messages`, `Read Message History`
        *   Voice: `Connect`, `Speak`
6.  生成されたURLを使ってBotをサーバーに招待する。

### 2. 環境変数の設定

1.  `.env.example` をコピーして `.env` ファイルを作成します。
    ```bash
    cp .env.example .env
    ```
2.  `.env` ファイルを編集し、取得したトークンや設定を記述します。

    ```ini
    # TTS Botのトークン
    DISCORD_TTS_BOT_TOKEN=your_tts_bot_token_here

    # Music Botのトークン
    DISCORD_MUSIC_BOT_TOKEN=your_music_bot_token_here

    # VOICEVOX設定
    VOICEVOX_URL=http://voicevox-engine:50021
    VOICEVOX_SPEAKER_ID=1  # 1: ずんだもん, 3: 四国めたん, etc.

    # Music Bot設定
    COMMAND_PREFIX=!
    DEFAULT_VOLUME=0.2
    DISCONNECT_TIMEOUT=300
    ```

### 3. 音楽ファイルの準備

プロジェクトのルートディレクトリに `music` というフォルダを作成し、再生したいMP3ファイルを配置してください。

```bash
mkdir music
# ここに .mp3 ファイルをコピーしてください
```

## 起動方法

Docker Composeを使用して、すべてのサービス（TTS Bot, Music Bot, Voicevox Engine）を一括起動します。

```bash
docker-compose up --build -d
```

*   **TTS Bot コンテナ**: `discord_tts_bot`
*   **Music Bot コンテナ**: `discord_music_bot`
*   **Voicevox Engine**: `voicevox_engine`

停止する場合：
```bash
docker-compose down
```

## コマンド一覧

### 🗣️ TTS Bot コマンド

| コマンド | 説明 |
| :--- | :--- |
| `/summon` | コマンド実行者がいるボイスチャンネルに参加し、そのテキストチャンネルの読み上げを開始します。 |
| `/q` | ボイスチャンネルから退出します（「サラダバー」と言って去ります）。 |

### 🎵 Music Bot コマンド

| コマンド | 説明 |
| :--- | :--- |
| `/join_y` | ボイスチャンネルに接続します。 |
| `/leave` | ボイスチャンネルから退出します。 |
| `/play <ファイル名>` | `music/` フォルダ内の指定したMP3ファイルを再生します。 |
| `/play_all` | `music/` フォルダ内の全曲をランダムな順序でキューに追加します。 |
| `/random` | `music/` フォルダ内からランダムに1曲選んでキューに追加します。 |
| `/nowplaying` | 現在再生中の曲名を表示します。 |
| `/queue` | 現在の再生待ちリストを表示します。 |
| `/pause` | 再生を一時停止します。 |
| `/resume` | 再生を再開します。 |
| `/stop` | 再生を停止し、キューをクリアします。 |
| `/skip` | 現在の曲をスキップします。 |
| `/volume <0-100>` | 音量を設定します (0-100)。 |
| `/seek <秒数>` | 指定した秒数へシークします。 |
| `/forward [秒数]` | 指定秒数だけ早送りします (デフォルト10秒)。 |
| `/backward [秒数]` | 指定秒数だけ巻き戻しします (デフォルト10秒)。 |

## ディレクトリ構成
```
.
├── docker-compose.yml
├── .env                 # 環境変数（Gitには含めない）
├── music/               # MP3ファイル置き場
├── src/
│   ├── ttsBot.py        # 読み上げBotのソース
│   └── musicBot.py      # 音楽Botのソース
└── docker/              # Dockerfile関連
```