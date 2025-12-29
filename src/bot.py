import os
import asyncio
import io
import discord
import aiohttp
from discord.ext import commands

# --- Opusライブラリがロードされているか確認 ---
if not discord.opus.is_loaded():
    print("Opusライブラリがロードされていません。")
else:
    print("Opusライブラリは正常にロードされています。")

# --- 環境変数 ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
VOICEVOX_URL = os.getenv('VOICEVOX_URL', 'http://localhost:50021')
SPEAKER_ID = os.getenv('VOICEVOX_SPEAKER_ID', 1)

# --- Botの基本設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# サーバーごとの状態を管理
server_states = {}


# --- VOICEVOX連携 ---
async def create_wav(text: str):
    """VOICEVOXエンジンと通信して音声WAVデータを生成する"""
    async with aiohttp.ClientSession() as session:
        try:
            # 1. audio_query
            params = {'text': text, 'speaker': SPEAKER_ID}
            print(f"[{text[:10]}...] 1/2: audio_query実行")
            async with session.post(f'{VOICEVOX_URL}/audio_query', params=params) as response:
                if response.status != 200:
                    print(f"Error: audio_query failed: {response.status}, {await response.text()}")
                    return None
                query_data = await response.json()
            print(f"[{text[:10]}...] 1/2: audio_query成功")

            # 2. synthesis
            headers = {'Content-Type': 'application/json'}
            print(f"[{text[:10]}...] 2/2: synthesis実行")
            async with session.post(f'{VOICEVOX_URL}/synthesis', params={'speaker': SPEAKER_ID}, json=query_data, headers=headers) as response:
                if response.status != 200:
                    print(f"Error: synthesis failed: {response.status}, {await response.text()}")
                    return None
                wav_data = await response.read()
                print(f"[{text[:10]}...] 2/2: synthesis成功 (サイズ: {len(wav_data)} bytes)")
                return io.BytesIO(wav_data)
        except aiohttp.ClientConnectorError as e:
            print(f"Error: VOICEVOX engine not found at {VOICEVOX_URL}. Details: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during wav creation: {e}")
            return None


# --- 読み上げワーカー ---
async def tts_worker(server_id: int):
    """サーバーごとの読み上げキューを処理する"""
    state = server_states.get(server_id)
    if not state:
        return

    print(f"[Server:{server_id}] TTSワーカーを開始しました。")
    q = state['queue']
    while True:
        try:
            text_to_speak = await q.get()
            print(f"[Server:{server_id}] キューからメッセージを取得: '{text_to_speak[:20]}...'")
            
            voice_client = state.get('voice_client')
            if not voice_client or not voice_client.is_connected():
                print(f"[Server:{server_id}] VoiceClientが見つからないか未接続のためスキップ。")
                q.task_done()
                continue

            wav_data = await create_wav(text_to_speak)
            if wav_data:
                source = discord.FFmpegPCMAudio(wav_data, pipe=True)
                
                while voice_client.is_playing():
                    print(f"[Server:{server_id}] 他の音声を再生中のため待機します。")
                    await asyncio.sleep(0.1)
                
                print(f"[Server:{server_id}] 音声の再生を開始します。")
                voice_client.play(source, after=lambda e: print(f'[Server:{server_id}] 再生完了。エラー: {e}') if e else print(f'[Server:{server_id}] 再生完了。'))
            else:
                print(f"[Server:{server_id}] WAVデータの生成に失敗したため、再生をスキップします。")
            
            q.task_done()
        except asyncio.CancelledError:
            print(f"[Server:{server_id}] TTSワーカーがキャンセルされました。")
            break
        except Exception as e:
            print(f"Error in TTS worker for server {server_id}: {e}")
            q.task_done()


# --- Botイベント ---
@bot.event
async def on_ready():
    """起動時にスラッシュコマンドを同期し、準備完了を通知する"""
    print(f'{bot.user.name} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        for server_id in server_states:
            if 'task' in server_states[server_id] and server_states[server_id]['task'].done():
                 print(f"[Server:{server_id}] 停止していたTTSワーカーを再開します。")
                 server_states[server_id]['task'] = asyncio.create_task(tts_worker(server_id))
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    """メッセージを検知して読み上げキューに追加する"""
    if message.author == bot.user:
        return

    if message.content.startswith(bot.command_prefix):
         await bot.process_commands(message)
         return
    
    if not message.guild:
        return
    
    server_id = message.guild.id
    state = server_states.get(server_id)
    if state and state.get('text_channel') and state['text_channel'].id == message.channel.id:
        if message.content:
            print(f"[Server:{server_id}] メッセージをキューに追加: '{message.clean_content[:20]}...'")
            await state['queue'].put(message.clean_content)


# --- スラッシュコマンド ---
@bot.tree.command(name="summon", description="あなたのいるボイスチャンネルに参加して、このテキストチャンネルの読み上げを開始します。")
async def summon(interaction: discord.Interaction):
    """コマンド実行者がいるボイスチャンネルに参加する"""
    if not interaction.guild:
        await interaction.response.send_message("サーバー内でのみ実行できます。", ephemeral=True)
        return
        
    server_id = interaction.guild.id
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("先にボイスチャンネルに参加してください。", ephemeral=True)
        return

    voice_channel = interaction.user.voice.channel
    text_channel = interaction.channel

    if server_id in server_states and server_states[server_id].get('voice_client'):
        vc = server_states[server_id]['voice_client']
        if vc.is_connected():
            if vc.channel.id != voice_channel.id:
                await vc.move_to(voice_channel)
                await interaction.response.send_message(f"{voice_channel.name} に移動しました。")
            else:
                await interaction.response.send_message("既に接続済みです。", ephemeral=True)
            server_states[server_id]['text_channel'] = text_channel
            print(f"[Server:{server_id}] 監視対象のテキストチャンネルを {text_channel.name} に変更しました。")
            # キューをリセットして入室メッセージを追加
            server_states[server_id]['queue'] = asyncio.Queue()
            await server_states[server_id]['queue'].put("シフトはいりまーす")
            return
    
    try:
        vc = await voice_channel.connect()
        
        if server_id not in server_states:
            server_states[server_id] = {
                'queue': asyncio.Queue()
            }
            server_states[server_id]['task'] = asyncio.create_task(tts_worker(server_id))

        server_states[server_id]['voice_client'] = vc
        server_states[server_id]['text_channel'] = text_channel
        
        # キューをリセットして入室メッセージを追加
        server_states[server_id]['queue'] = asyncio.Queue()
        await server_states[server_id]['queue'].put("シフトはいりまーす")
        
        await interaction.response.send_message(f"`{voice_channel.name}` に参加し、このチャンネルの読み上げを開始します。")
        print(f"[Server:{server_id}] {voice_channel.name} に接続し、{text_channel.name} の監視を開始しました。")

    except Exception as e:
        await interaction.response.send_message(f"接続に失敗しました: {e}", ephemeral=True)


@bot.tree.command(name="q", description="ボイスチャンネルから退出します。")
async def dismiss(interaction: discord.Interaction):
    """ボイスチャンネルから切断する"""
    if not interaction.guild:
        await interaction.response.send_message("サーバー内でのみ実行できます。", ephemeral=True)
        return

    server_id = interaction.guild.id
    state = server_states.get(server_id)

    if not state or not state.get('voice_client') or not state['voice_client'].is_connected():
        await interaction.response.send_message("ボットは現在ボイスチャンネルにいません。", ephemeral=True)
        return

    vc = state['voice_client']
    
    # 先にインタラクションに応答しておく
    await interaction.response.send_message("サラダバー")

    # --- 再生終了後に切断とクリーンアップを行う非同期関数 ---
    async def disconnect_after_play(error):
        if error:
            print(f"Playback error before disconnect: {error}")
        
        if vc.is_connected():
            await vc.disconnect()

        if 'task' in state:
            state['task'].cancel()
        
        if server_id in server_states:
            del server_states[server_id]

        print(f"[Server:{server_id}] ボイスチャンネルから切断しました。")

    # --- 「サラダバー」の音声を生成・再生 ---
    wav_data = await create_wav("サラダバー")
    if wav_data and vc.is_connected():
        source = discord.FFmpegPCMAudio(wav_data, pipe=True)
        # 再生中の場合は待機
        while vc.is_playing():
            await asyncio.sleep(0.1)
        # 再生し、終了後に関数を呼び出す
        vc.play(source, after=lambda e: bot.loop.create_task(disconnect_after_play(e)))
    else:
        # 音声生成に失敗した場合は、即座に切断処理を呼び出す
        await disconnect_after_play(None)


# --- Bot実行 ---
if __name__ == "__main__":
    if not TOKEN:
        print("エラー: DISCORD_BOT_TOKENが見つかりません。")
    elif not VOICEVOX_URL:
        print("エラー: VOICEVOX_URLが見つかりません。")
    else:
        bot.run(TOKEN)
