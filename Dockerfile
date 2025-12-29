# Python 3.10をベースイメージとして使用
FROM python:3.10-slim

# ffmpegをインストール
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libopus0

# 作業ディレクトリを設定
WORKDIR /app

# 音声ファイルの出力先ディレクトリを作成
RUN mkdir /app/audio_out

# 依存関係をインストールするためにrequirements.txtをコピー
COPY requirements.txt .

# pipをアップグレードし、依存関係をインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ソースコードをコンテナにコピー
COPY ./src .

# ボットを実行するコマンド
CMD ["python", "bot.py"]
