import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp as youtube_dl

# Cargar variables de entorno
load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Configuración de Spotify
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id,
                                                                client_secret=spotify_client_secret))

# Configuración del bot de Discord
intents = discord.Intents.default()
intents.message_content = True  # Habilitar el intent de contenido de mensajes
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cola de canciones
song_queue = []

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command(name='info')
async def info_command(ctx):
    info_text = """
    Yuu se la come
    """
    await ctx.send(info_text)

@bot.command(name='play')
async def play_command(ctx, *, url):
    try:
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
            return

        if not ctx.voice_client:
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        track_id = url.split("/")[-1].split("?")[0]
        track = spotify.track(track_id)
        track_name = track['name']
        track_artists = ", ".join([artist['name'] for artist in track['artists']])

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{track_name} {track_artists}", download=False)
            url2 = info['entries'][0]['url']

        song_queue.append((url2, track_name, track_artists))

        if not vc.is_playing():
            await play_next_song(ctx)

        await ctx.send(f"Agregado a la cola: {track_name} por {track_artists}")
    except Exception as e:
        await ctx.send(f"Error al intentar reproducir la canción: {e}")

async def play_next_song(ctx):
    if song_queue:
        url, track_name, track_artists = song_queue.pop(0)
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=url), after=lambda e: bot.loop.create_task(play_next_song(ctx)))
        await ctx.send(f"Reproduciendo {track_name} por {track_artists}")

@bot.command(name='quit')
async def quit_command(ctx):
    await ctx.send("Ya me voy alv")
    song_queue.clear()
    await ctx.voice_client.disconnect()

# Configuración de FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.on_event("startup")
async def startup_event():
    await bot.start(discord_token)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
