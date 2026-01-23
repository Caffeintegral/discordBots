import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import time
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_MUSIC_BOT_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.2'))
DISCONNECT_TIMEOUT = int(os.getenv('DISCONNECT_TIMEOUT', '300'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# 再生状態を管理するクラス
class MusicPlayerState:
    def __init__(self):
        self.current_file = None
        self.start_time = 0
        self.pause_time = 0
        self.elapsed_before_pause = 0
        self.volume = DEFAULT_VOLUME
        self.queue = []  # 再生キュー
        self.is_seeking = False  # シーク中かどうかのフラグ
        self.text_channel = None  # 通知用テキストチャンネル
        self.timeout_task = None  # 自動切断用タスク

music_player_states = {}

def get_music_state(guild_id):
    if guild_id not in music_player_states:
        music_player_states[guild_id] = MusicPlayerState()
    return music_player_states[guild_id]

async def disconnect_timer(guild):
    """指定時間待機後に切断するタスク"""
    await asyncio.sleep(DISCONNECT_TIMEOUT)
    state = get_music_state(guild.id)
    if guild.voice_client and guild.voice_client.is_connected():
        await guild.voice_client.disconnect()
        if state.text_channel:
            await state.text_channel.send("一定時間操作がなかったため退出しました。")
        if guild.id in music_player_states:
            del music_player_states[guild.id]

def cancel_timeout(state):
    if state.timeout_task:
        state.timeout_task.cancel()
        state.timeout_task = None

def start_timeout(guild):
    state = get_music_state(guild.id)
    cancel_timeout(state)
    state.timeout_task = bot.loop.create_task(disconnect_timer(guild))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (Music Bot)')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="join_y", description="ボイスチャンネルに接続")
async def join_y(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"{channel.name} に接続しました。")
        start_timeout(interaction.guild)
    else:
        await interaction.response.send_message("ボイスチャンネルに接続してからコマンドを打ってください。", ephemeral=True)

@bot.tree.command(name="leave", description="ボイスチャンネルから退出")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        state = get_music_state(interaction.guild.id)
        cancel_timeout(state)
        await interaction.guild.voice_client.disconnect()
        if interaction.guild.id in music_player_states:
            del music_player_states[interaction.guild.id]
        await interaction.response.send_message("退出しました。")
    else:
        await interaction.response.send_message("Botはボイスチャンネルに接続していません。", ephemeral=True)

async def play_next(guild):
    """キューから次の曲を取り出して再生"""
    state = get_music_state(guild.id)
    if state.queue:
        cancel_timeout(state)
        next_file = state.queue.pop(0)
        if state.text_channel:
            await play_audio(guild, state.text_channel, next_file)
    else:
        state.current_file = None
        start_timeout(guild)
        # キューが空になったら何もしない（待機）

async def play_audio(guild, text_channel, filename, seek_time=0):
    state = get_music_state(guild.id)
    state.current_file = filename
    state.start_time = time.time() - seek_time
    state.elapsed_before_pause = seek_time

    voice_client = guild.voice_client
    if voice_client and voice_client.is_playing():
        state.is_seeking = True  # シークによる停止であることをフラグで示す
        voice_client.stop()

    ffmpeg_options = {
        'before_options': f'-ss {seek_time}',
        'options': '-vn'
    }
    
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(filename, **ffmpeg_options),
        volume=state.volume
    )
    
    def after_playing(error):
        if error:
            print(f'Player error: {error}')
        
        # シーク中の停止なら次の曲へ行かない
        if state.is_seeking:
            state.is_seeking = False
            return

        # 次の曲を再生（非同期関数を呼び出すための処理）
        coro = play_next(guild)
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Error scheduling next song: {e}")

    if voice_client:
        voice_client.play(source, after=after_playing)
    
    # シーク再生でなければメッセージを表示
    if seek_time == 0:
        await text_channel.send(f'再生開始: {filename}')

@bot.tree.command(name="play", description="MP3ファイルを再生 (例: music.mp3)")
async def play(interaction: discord.Interaction, filename: str):
    # musicディレクトリも検索対象にする
    target_file = filename
    if not os.path.exists(target_file):
        if os.path.exists(os.path.join('music', filename)):
            target_file = os.path.join('music', filename)
        else:
            await interaction.response.send_message(f"ファイルが見つかりません: {filename}", ephemeral=True)
            return

    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("ボイスチャンネルに接続してください。", ephemeral=True)
            return

    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    state.queue.append(target_file)
    
    # 再生中でなければすぐに再生開始
    if not interaction.guild.voice_client.is_playing() and not interaction.guild.voice_client.is_paused():
        await play_next(interaction.guild)
        await interaction.response.send_message(f"再生リクエストを受け付けました: {filename}")
    else:
        await interaction.response.send_message(f"キューに追加しました: {filename}")

@bot.tree.command(name="play_all", description="musicディレクトリ内の全曲をランダムな順番で再生")
async def play_all(interaction: discord.Interaction):
    music_dir = 'music'
    if not os.path.exists(music_dir):
        await interaction.response.send_message("musicディレクトリが見つかりません。", ephemeral=True)
        return

    files = [f for f in os.listdir(music_dir) if f.lower().endswith('.mp3')]
    if not files:
        await interaction.response.send_message("musicディレクトリにMP3ファイルが見つかりません。", ephemeral=True)
        return

    random.shuffle(files)
    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    for f in files:
        state.queue.append(os.path.join(music_dir, f))
    
    await interaction.response.send_message(f"{len(files)}曲をランダムな順番でキューに追加しました。")

    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            # 接続できない場合はここで終了
            return

    if not interaction.guild.voice_client.is_playing() and not interaction.guild.voice_client.is_paused():
        await play_next(interaction.guild)

@bot.tree.command(name="random", description="musicディレクトリ内の曲をランダムに再生")
async def random_play(interaction: discord.Interaction):
    music_dir = 'music'
    if not os.path.exists(music_dir):
        await interaction.response.send_message("musicディレクトリが見つかりません。", ephemeral=True)
        return

    files = [f for f in os.listdir(music_dir) if f.lower().endswith('.mp3')]
    if not files:
        await interaction.response.send_message("musicディレクトリにMP3ファイルが見つかりません。", ephemeral=True)
        return

    target_file = os.path.join(music_dir, random.choice(files))

    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("ボイスチャンネルに接続してください。", ephemeral=True)
            return

    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    state.queue.append(target_file)

    # 再生中でなければすぐに再生開始
    if not interaction.guild.voice_client.is_playing() and not interaction.guild.voice_client.is_paused():
        await play_next(interaction.guild)
        await interaction.response.send_message(f"ランダム再生リクエスト: {os.path.basename(target_file)}")
    else:
        await interaction.response.send_message(f"キューに追加しました: {os.path.basename(target_file)}")

@bot.tree.command(name="nowplaying", description="現在再生中の曲名を表示")
async def nowplaying(interaction: discord.Interaction):
    state = get_music_state(interaction.guild.id)
    if state.current_file:
        filename = os.path.basename(state.current_file)
        await interaction.response.send_message(f"🎵 現在再生中: {filename}")
    else:
        await interaction.response.send_message("現在再生中の曲はありません。")

@bot.tree.command(name="queue", description="現在の再生キューを表示")
async def queue(interaction: discord.Interaction):
    state = get_music_state(interaction.guild.id)
    if not state.queue:
        await interaction.response.send_message("現在のキューは空です。")
        return

    queue_list = []
    for i, file_path in enumerate(state.queue[:10], 1):
        filename = os.path.basename(file_path)
        queue_list.append(f"{i}. {filename}")

    if len(state.queue) > 10:
        queue_list.append(f"...他 {len(state.queue) - 10} 曲")

    msg = "\n".join(queue_list)
    await interaction.response.send_message(f"**再生キュー:**\n{msg}")

@bot.tree.command(name="pause", description="再生を中断")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        state = get_music_state(interaction.guild.id)
        state.pause_time = time.time()
        await interaction.response.send_message("一時停止しました。")
        start_timeout(interaction.guild)
    else:
        await interaction.response.send_message("再生中ではありません。", ephemeral=True)

@bot.tree.command(name="resume", description="再生を再開")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        state = get_music_state(interaction.guild.id)
        cancel_timeout(state)
        # 中断していた時間を加算して開始時間を調整
        state.start_time += (time.time() - state.pause_time)
        vc.resume()
        await interaction.response.send_message("再生を再開しました。")
    else:
        await interaction.response.send_message("一時停止中ではありません。", ephemeral=True)

@bot.tree.command(name="stop", description="再生を停止")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        state = get_music_state(interaction.guild.id)
        state.queue.clear()  # キューもクリア
        state.current_file = None
        vc.stop()
        await interaction.response.send_message("再生を停止し、キューをクリアしました。")
    else:
        await interaction.response.send_message("Botは接続していません。", ephemeral=True)

@bot.tree.command(name="skip", description="現在の曲をスキップ")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("スキップしました。")
    else:
        await interaction.response.send_message("再生中ではありません。", ephemeral=True)

@bot.tree.command(name="volume", description="音量を変更 (0-100)")
async def volume(interaction: discord.Interaction, vol: int):
    vc = interaction.guild.voice_client
    if vc and vc.source:
        new_vol = vol / 100
        vc.source.volume = new_vol
        get_music_state(interaction.guild.id).volume = new_vol
        await interaction.response.send_message(f"音量を {vol}% に変更しました。")
    else:
        await interaction.response.send_message("音楽を再生していません。", ephemeral=True)

@bot.tree.command(name="forward", description="指定秒数進む")
async def forward(interaction: discord.Interaction, seconds: int = 10):
    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    if state.current_file and interaction.guild.voice_client:
        current_pos = time.time() - state.start_time
        await play_audio(interaction.guild, interaction.channel, state.current_file, seek_time=current_pos + seconds)
        await interaction.response.send_message(f"{seconds}秒進みました。")
    else:
        await interaction.response.send_message("再生中ではありません。", ephemeral=True)

@bot.tree.command(name="backward", description="指定秒数戻る")
async def backward(interaction: discord.Interaction, seconds: int = 10):
    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    if state.current_file and interaction.guild.voice_client:
        current_pos = time.time() - state.start_time
        new_pos = max(0, current_pos - seconds)
        await play_audio(interaction.guild, interaction.channel, state.current_file, seek_time=new_pos)
        await interaction.response.send_message(f"{seconds}秒戻りました。")
    else:
        await interaction.response.send_message("再生中ではありません。", ephemeral=True)

@bot.tree.command(name="seek", description="指定した秒数へ移動")
async def seek(interaction: discord.Interaction, seconds: int):
    state = get_music_state(interaction.guild.id)
    state.text_channel = interaction.channel
    if state.current_file and interaction.guild.voice_client:
        await play_audio(interaction.guild, interaction.channel, state.current_file, seek_time=seconds)
        await interaction.response.send_message(f"{seconds}秒地点へ移動しました。")
    else:
        await interaction.response.send_message("再生中ではありません。", ephemeral=True)

@bot.tree.command(name="help", description="コマンド一覧を表示")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Music Bot コマンド一覧", color=discord.Color.blue())
    embed.add_field(name="/join_y", value="ボイスチャンネルに接続します。", inline=False)
    embed.add_field(name="/leave", value="ボイスチャンネルから退出します。", inline=False)
    embed.add_field(name="/play <ファイル名>", value="指定したMP3ファイルを再生します。", inline=False)
    embed.add_field(name="/play_all", value="musicフォルダ内の全曲をランダム順で再生します。", inline=False)
    embed.add_field(name="/random", value="musicフォルダ内からランダムに1曲再生します。", inline=False)
    embed.add_field(name="/nowplaying", value="現在再生中の曲名を表示します。", inline=False)
    embed.add_field(name="/queue", value="再生待ちリストを表示します。", inline=False)
    embed.add_field(name="/pause", value="再生を一時停止します。", inline=False)
    embed.add_field(name="/resume", value="再生を再開します。", inline=False)
    embed.add_field(name="/stop", value="再生を停止し、キューをクリアします。", inline=False)
    embed.add_field(name="/skip", value="現在の曲をスキップします。", inline=False)
    embed.add_field(name="/volume <0-100>", value="音量を変更します。", inline=False)
    embed.add_field(name="/forward [秒数]", value="指定秒数進みます。", inline=False)
    embed.add_field(name="/backward [秒数]", value="指定秒数戻ります。", inline=False)
    embed.add_field(name="/seek <秒数>", value="指定した秒数へ移動します。", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("エラー: 環境変数 DISCORD_MUSIC_BOT_TOKEN が設定されていません。.envファイルを確認してください。")
    else:
        bot.run(TOKEN)