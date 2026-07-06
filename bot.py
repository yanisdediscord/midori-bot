import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

# -------------------
# LOAD .ENV
# -------------------
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN:
    raise ValueError("❌ TOKEN manquant dans .env")

if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID manquant dans .env")

CHANNEL_ID = int(CHANNEL_ID)

# 🎧 SALON VOCAL AFK FIXE
AFK_VOICE_CHANNEL_ID = 1523486632681017414

# -------------------
# INTENTS
# -------------------
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

MESSAGE_ID = None


# -------------------
# STATS
# -------------------
def get_stats(guild: discord.Guild):
    members = guild.member_count

    online = sum(
        1 for m in guild.members
        if m.status != discord.Status.offline
    )

    voice = sum(len(vc.members) for vc in guild.voice_channels)

    streaming = sum(
        1 for m in guild.members
        for a in m.activities
        if isinstance(a, discord.Streaming)
    )

    boosts = guild.premium_subscription_count

    return members, online, voice, streaming, boosts


# -------------------
# EMBED BUILDER
# -------------------
def build_embed(guild: discord.Guild):
    members, online, voice, streaming, boosts = get_stats(guild)

    icon = guild.icon.url if guild.icon else None

    embed = discord.Embed(
        title=f"{guild.name} • Statistiques",
        description="🌐 .gg/midori",
        color=discord.Color.dark_theme()
    )

    if icon:
        embed.set_thumbnail(url=icon)

    embed.add_field(name="👥 Membres", value=f"`{members}`", inline=True)
    embed.add_field(name="🟢 En ligne", value=f"`{online}`", inline=True)
    embed.add_field(name="🎧 En vocal", value=f"`{voice}`", inline=True)

    embed.add_field(name="📡 En stream", value=f"`{streaming}`", inline=True)
    embed.add_field(name="🚀 Boosts", value=f"`{boosts}`", inline=True)

    embed.set_footer(text="Mise à jour automatique toutes les 24h")

    return embed


# -------------------
# READY EVENT
# -------------------
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name=".gg/midori")
    )

    # 🔥 JOIN AUTO AFK VOICE
    await join_afk_voice()

    update_stats.start()


# -------------------
# AFK VOICE SYSTEM
# -------------------
async def join_afk_voice():
    await bot.wait_until_ready()

    channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)

    if channel is None:
        print("❌ Salon vocal AFK introuvable")
        return

    # si déjà connecté → ignore
    if bot.voice_clients:
        print("🎧 Déjà en vocal")
        return

    await channel.connect()
    print("🎧 Bot connecté en AFK vocal")


# -------------------
# LOOP 24H
# -------------------
@tasks.loop(hours=24)
async def update_stats():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Salon introuvable")
        return

    embed = build_embed(channel.guild)

    global MESSAGE_ID

    if MESSAGE_ID is None:
        msg = await channel.send(embed=embed)
        MESSAGE_ID = msg.id
    else:
        try:
            msg = await channel.fetch_message(MESSAGE_ID)
            await msg.edit(embed=embed)
        except discord.NotFound:
            msg = await channel.send(embed=embed)
            MESSAGE_ID = msg.id


# -------------------
# RUN
# -------------------
bot.run(TOKEN)