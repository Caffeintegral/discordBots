# Gemini Project Context: Discord Bots (TTS & Music)

## Project Overview

This project consists of two distinct Discord bots managed within a single repository:
1.  **Japanese TTS Bot**: A Text-to-Speech bot that uses the `discord.py` library and connects to a locally hosted VOICEVOX engine to generate Japanese speech from text messages.
2.  **Music Bot**: A bot for playing local MP3 files from a `music/` directory, supporting playback controls like seek, volume, and queue management.

The entire application is containerized using Docker and managed with Docker Compose, running three separate networked services: the TTS bot, the Music bot, and the VOICEVOX engine.

## Key Technologies & Architecture

-   **Application Language**: Python 3.10
-   **Core Library**: `discord.py` for Discord API interaction and slash command support.
-   **Audio Processing**: `FFmpeg` is used by both bots for audio streaming and manipulation (seeking, volume adjustment).
-   **TTS Engine**: `VOICEVOX` (running in a CPU-based Docker container) provides the speech synthesis API.
-   **State Management**:
    -   `ttsBot.py`: Manages per-server state (voice client, text channel, message queue) in a `server_states` dictionary.
    -   `musicBot.py`: Uses a `MusicPlayerState` class and a `music_player_states` dictionary to track playback position, volume, and song queues.
-   **Containerization**:
    -   `discord-tts-bot`: Python environment with `ffmpeg` and `libopus0`.
    -   `discord-music-bot`: Python environment with `ffmpeg`.
    -   `voicevox-engine`: The TTS engine API service.

## Project Structure

-   `src/ttsBot.py`: Main logic for the TTS bot.
-   `src/musicBot.py`: Main logic for the Music bot.
-   `docker/`: Contains Dockerfiles for both bots (`tts/Dockerfile`, `music/Dockerfile`).
-   `music/`: Local directory for MP3 files (ignored by git).
-   `docker-compose.yml`: Defines the multi-container orchestration.
-   `.env`: Stores sensitive tokens and configuration for both bots.

## Development Conventions

-   **Asynchronous Code**: Built on `asyncio`. Both bots handle concurrent requests per server.
-   **Commands**: Both bots exclusively use Discord Slash Commands (`bot.tree.command`).
-   **Logging**: Uses `print` statements; `PYTHONUNBUFFERED=1` is set in Docker to ensure logs are visible in real-time.
-   **Graceful Handling**:
    -   TTS Bot: Plays a "Salad bar" farewell message before disconnecting.
    -   Music Bot: Includes an automatic disconnect timer (`DISCONNECT_TIMEOUT`) when idle.
-   **Terminology**: Uses "Server" in logs and variables to refer to Discord Guilds.

## Building and Running

```shell
# Start everything
docker-compose up --build -d

# Stop everything
docker-compose down
```