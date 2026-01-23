# Python 3.10をベースイメージとして使用
FROM python:3.10-slim

# ffmpegとlibopusをインストール
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libopus0

# 作業ディレクトリを設定
WORKDIR /app

# 音声ファイルの出力先ディレクトリを作成
RUN mkdir /app/audio_out

# 依存関係のインストールとソースコードのコピー
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .

# TTSボットを実行
CMD ["python", "src/ttsBot.py"]