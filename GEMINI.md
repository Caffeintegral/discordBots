# Gemini Project Context: Discord TTS Bot

## Project Overview

This project is a Japanese Text-to-Speech (TTS) bot for Discord. It uses the `discord.py` library to interact with Discord and connects to a locally hosted VOICEVOX engine to generate Japanese speech from text messages. The entire application is containerized using Docker and managed with Docker Compose, running the bot and the VOICEVOX engine as two separate, networked services.

The bot listens for slash commands (`/summon`, `/q`) to join and leave voice channels. Once in a channel, it monitors a specific text channel and reads out any messages sent there. It also has custom welcome and farewell messages when joining or leaving a voice channel.

## Key Technologies & Architecture

-   **Application Language:** Python 3.10
-   **Core Library:** `discord.py` for Discord API interaction.
-   **HTTP Client:** `aiohttp` for asynchronous requests to the VOICEVOX API.
-   **TTS Engine:** `VOICEVOX`, running in a separate Docker container (`voicevox/voicevox_engine:cpu-latest`).
-   **Containerization:** Docker & Docker Compose.
    -   `discord-bot`: The main Python application container. It has `ffmpeg` and `libopus0` installed for audio processing and encoding.
    -   `voicevox-engine`: The TTS engine, which exposes its API on port `50021`.
-   **Configuration:** Environment variables are loaded from a `.env` file using `python-dotenv`. Key variables include `DISCORD_BOT_TOKEN`, `VOICEVOX_URL`, and `VOICEVOX_SPEAKER_ID`.

## Building and Running

1.  **Environment Setup:**
    *   Create a `.env` file from the `.env.example` template.
    *   Populate the `DISCORD_BOT_TOKEN` with a valid Discord bot token.
    *   Optionally, change `VOICEVOX_SPEAKER_ID` to select a different VOICEVOX character.

2.  **Build and Run:**
    *   The project is started using Docker Compose. The following command will build the bot's Docker image and start both the bot and VOICEVOX engine containers in detached mode.

    ```shell
    docker-compose up --build -d
    ```

3.  **Stopping:**
    ```shell
    docker-compose down
    ```

## Development Conventions

-   **Project Structure:** Application source code is located in the `src/` directory.
-   **Dependencies:** Python dependencies are managed in `requirements.txt`. System-level dependencies (`ffmpeg`, `libopus0`) are defined in the `Dockerfile`.
-   **Asynchronous Code:** The entire application is built on Python's `asyncio` framework to handle I/O-bound operations efficiently.
-   **State Management:** The bot maintains the state for each server (voice client, text channel, message queue) in a global dictionary (`server_states`).
-   **Commands:** Bot commands are implemented as slash commands using `bot.tree.command()`.
-   **Terminology:** For code clarity and user-friendliness, the term "server" is used in variables and logs instead of the API term "guild".
-   **Logging:** The bot uses `print` statements for logging. Output buffering is disabled in Docker via the `PYTHONUNBUFFERED=1` environment variable.
-   **TTS Queue:** A message queue (`asyncio.Queue`) is implemented for each server to ensure messages are spoken sequentially.
-   **Graceful Exit:** The `/q` (dismiss) command is designed to play a farewell message completely before disconnecting from the voice channel, using an `after` callback on the `play()` method.
