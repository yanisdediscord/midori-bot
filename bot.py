import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN:
    raise ValueError("❌ TOKEN manquant")

CHANNEL_ID = int(CHANNEL_ID)

AFK_VOICE_CHANNEL_ID = 1523486632681017414

# -------------------
# BOT
# -------------------
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

MESSAGE_ID = None


# -------------------
# STATS
# -------------------
def get_stats(guild):
    membres = guild.member_count
    en_ligne = sum(1 for m in guild.members if m.status != discord.Status.offline)
    vocal = sum(len(vc.members) for vc in guild.voice_channels)

    stream = sum(
        1 for m in guild.members
        if m.voice and getattr(m.voice, "self_stream", False)
    )

    boosts = guild.premium_subscription_count

    return membres, en_ligne, vocal, stream, boosts


# -------------------
# EMBED STATS
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

    embed.add_field(name="👥 Membres", value=f"{members}", inline=True)
    embed.add_field(name="🟢 En ligne", value=f"{online}", inline=True)
    embed.add_field(name="🎧 En vocal", value=f"{voice}", inline=True)

    embed.add_field(name="📡 En stream", value=f"{streaming}", inline=True)
    embed.add_field(name="🚀 Boosts", value=f"{boosts}", inline=True)

    embed.set_footer(text="Mise à jour automatique toutes les 24h")

    return embed


# -------------------
# READY
# -------------------
@bot.event
async def on_ready():
    print(f"✅ Connecté : {bot.user}")

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name=".gg/midorii")
    )

    await join_afk()
    update_stats.start()


# -------------------
# AFK VOICE
# -------------------
async def join_afk():
    await bot.wait_until_ready()

    channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)

    if not channel:
        print("❌ Salon AFK introuvable")
        return

    if bot.voice_clients:
        return

    await channel.connect()
    print("🎧 Connecté au vocal AFK")


# -------------------
# STATS LOOP
# -------------------
@tasks.loop(hours=24)
async def update_stats():
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
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
        except:
            msg = await channel.send(embed=embed)
            MESSAGE_ID = msg.id


# -------------------
# HELPALL STYLÉ
# -------------------
@bot.command()
async def helpall(ctx):

    embed = discord.Embed(
        title="💎 MENU D'AIDE COMPLET",
        description="Commandes du serveur Midori",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="📁 SALONS",
        value="""
`+verrouiller` 🔒 Bloquer un salon
`+déverrouiller` 🔓 Débloquer un salon
`+cacher` 👁️ Masquer un salon
`+afficher` 👁️ Afficher un salon
`+renommer` ✏️ Renommer un salon
`+supprimer` 🗑️ Supprimer un salon
`+slowmode` 🐢 Mode lent
        """,
        inline=False
    )

    embed.add_field(
        name="🛡️ MODÉRATION",
        value="""
`+ban` ⛔ Bannir un membre
`+kick` 👢 Expulser un membre
`+mute` 🔇 Rendre muet
`+unmute` 🔊 Retirer muet
`+warn` ⚠️ Avertir un membre
`+unban` ✅ Débannir
        """,
        inline=False
    )

    embed.add_field(
        name="🎭 RÔLES",
        value="""
`+ajoutrerole` ➕ Ajouter un rôle
`+retirerole` ➖ Retirer un rôle
        """,
        inline=False
    )

    embed.add_field(
        name="📝 NOTES",
        value="""
`+ajoutenote` 📝 Ajouter une note
`+notes` 📌 Voir les notes
        """,
        inline=False
    )

    embed.set_footer(text="Midorii’ #🌸")

    await ctx.send(embed=embed)


# -------------------
# SALONS
# -------------------
@bot.command()
@commands.has_permissions(manage_channels=True)
async def verrouiller(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Salon verrouillé")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def déverrouiller(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Salon déverrouillé")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def cacher(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send("👁️ Salon caché")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def afficher(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send("👁️ Salon affiché")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renommer(ctx, *, nom):
    await ctx.channel.edit(name=nom)
    await ctx.send("✏️ Salon renommé")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def supprimer(ctx):
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, secondes: int):
    await ctx.channel.edit(slowmode_delay=secondes)
    await ctx.send(f"🐢 Mode lent : {secondes}s")


# -------------------
# MODÉRATION
# -------------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, raison=None):
    await member.ban(reason=raison)
    await ctx.send(f"⛔ {member} banni")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"👢 {member} expulsé")


# -------------------
# 🔇 MUTE PROPRE
# -------------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="🔇 Muet")

    if not role:
        role = await ctx.guild.create_role(name="🔇 Muet")

        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)
    await ctx.send(f"🔇 {member} est maintenant muet")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="🔇 Muet")

    if role:
        await member.remove_roles(role)
        await ctx.send(f"🔊 {member} n'est plus muet")


# -------------------
# RÔLES
# -------------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def ajoutrerole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send("➕ Rôle ajouté")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def retirerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send("➖ Rôle retiré")


# -------------------
# NOTES
# -------------------
notes = {}

@bot.command()
async def ajoutenote(ctx, member: discord.Member, *, texte):
    notes.setdefault(member.id, []).append(texte)
    await ctx.send("📝 Note ajoutée")

@bot.command()
async def notes(ctx, member: discord.Member):
    await ctx.send(f"📌 Notes : {notes.get(member.id, [])}")


# -------------------
# RUN
# -------------------
bot.run(TOKEN)
