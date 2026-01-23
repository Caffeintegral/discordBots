# Discord 読み上げBot

Discordのボイスチャンネルで、テキストメッセージをVOICEVOXエンジンを利用して読み上げるためのBotです。

## 機能

-   指定したテキストチャンネルに投稿されたメッセージを、ボイスチャンネルでリアルタイムに読み上げます。
-   ボイスチャンネル参加時に「シフトはいりまーす」と挨拶します。
-   ボイスチャンネル退出時に「サラダバー」と挨拶します。

## 必要なもの

-   Docker
-   Docker Compose

## Botの招待

Botをサーバーに招待し、正しく動作させるための手順です。

1.  [Discord Developer Portal](https://discord.com/developers/applications) を開き、対象のApplicationを選択します。
2.  **Bot** タブを開き、**Privileged Gateway Intents** セクションにある **Message Content Intent** を有効（ON）にして、変更を保存します。（読み上げやコマンド認識に必要です）
3.  左メニューの **OAuth2** -> **URL Generator** をクリックします。
4.  **SCOPES** の項目で、`bot` と `applications.commands` にチェックを入れます。
5.  **BOT PERMISSIONS** の項目が表示されるので、以下の権限にチェックを入れます。
    *   General Permissions: `View Channels`, `Send Messages`, `Read Message History`
    *   Voice Permissions: `Connect`, `Speak`
6.  一番下の **GENERATED URL** をコピーします。
7.  ブラウザでコピーしたURLを開き、招待したいサーバーを選択して認証します。

## セットアップ

1.  このリポジトリのファイルをダウンロードします。
2.  **Botトークンの取得:**
    1.  Discord Developer Portal にアクセスし、ログインします。
    2.  右上の "New Application" をクリックし、Botの名前を入力して作成します。
    3.  左側のメニューから "Bot" タブを選択します。
    4.  "Add Bot" をクリックし、確認画面で "Yes, do it!" をクリックします。
    5.  Botが作成されたら、"Token" セクションにある "Reset Token" をクリックします。
    6.  表示されたトークンをコピーします。**このトークンは他人に教えないでください。**
3.  `.env.example` ファイルをコピーして `.env` という名前のファイルを作成します。
4.  作成した `.env` ファイルをテキストエディタで開き、`DISCORD_TTS_BOT_TOKEN` の部分に手順2で取得したトークンを貼り付けます。
    ```env
    DISCORD_TTS_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"
    ```
5.  （任意）`VOICEVOX_SPEAKER_ID`の数値を変更することで、読み上げキャラクターを変更できます。デフォルトは `1`（ずんだもん）です。
    ```env
    # 例: 3に変更すると四国めたんになります
    VOICEVOX_SPEAKER_ID=3
    ```

## 使い方

1.  ファイルのトップディレクトリで、ターミナル（コマンドプロンプトやPowerShell）を開き、以下のコマンドを実行してbotを起動します。

    ```shell
    docker-compose up --build -d
    ```

2.  Discordサーバーでスラッシュコマンドを実行します。

## コマンド一覧

-   `/summon`
    -   コマンドを実行したユーザーがいるボイスチャンネルにbotが参加します。
    -   このコマンドが実行されたテキストチャンネルが、読み上げ対象になります。
-   `/q`
    -   botがボイスチャンネルから退出します。
