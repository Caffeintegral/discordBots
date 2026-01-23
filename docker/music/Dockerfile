# Python 3.10をベースイメージとして使用
FROM python:3.10-slim

# ffmpegをインストール
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係のインストールとソースコードのコピー
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .

# Musicボットを実行
CMD ["python", "src/musicBot.py"]