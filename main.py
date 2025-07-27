import discord
import os
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask
import threading
import aiohttp   # <-- এখানে ইমপোর্ট করুন
import asyncio
import json

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot is working Power by ! ＧＡＭＥＲ ＳＡＢＢＩＲ"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

load_dotenv()
TOKEN = os.getenv("TOKEN")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

client = MyClient()
registered_channels = {}
user_languages = {}
DEFAULT_LANG = "en"

@client.event
async def on_ready():
    load_registered_channels()  # 👈 এটুকু ঠিক
    await client.tree.sync()
    print(f"✅ Logged in as {client.user}")



registered_channels = {}

REGISTERED_CHANNELS_FILE = "registered_channels.json"


def save_registered_channels():
    with open(REGISTERED_CHANNELS_FILE, "w") as f:
        json.dump({str(k): v for k, v in registered_channels.items()}, f)

def load_registered_channels():
    global registered_channels
    try:
        with open(REGISTERED_CHANNELS_FILE, "r") as f:
            registered_channels = json.load(f)
            registered_channels = {int(k): int(v) for k, v in registered_channels.items()}
    except FileNotFoundError:
        registered_channels = {}





OWNER_ID = 1305989556256112702  # <-- তোমার ডিসকর্ড ID এখানে বসাও
like_enabled_channels = set()

@client.tree.command(name="likesetup", description="Activate like command in this channel (Owner only)")
async def likesetup(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        owner_mention = f"<@{OWNER_ID}>"
        await interaction.response.send_message(
            f"❌ শুধুমাত্র বট OWNER এই কমান্ড চালাতে পারবেন। POWER BY {owner_mention}",
            ephemeral=True
        )
        return

    like_enabled_channels.add(interaction.channel.id)  # ✅ ঠিক এটা
    await interaction.response.send_message(
        f"✅ এই চ্যানেলে এখন থেকে `/like` কমান্ড চালানো যাবে।",
        ephemeral=True
    )




# -------- /setup --------
@client.tree.command(name="setup", description="Register this channel for bot commands")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    channel = interaction.channel
    registered_channels[interaction.guild.id] = channel.id
    save_registered_channels()  # 👈 ঠিক করলাম
    await interaction.response.send_message(
        f"✅ This channel {channel.mention} is now registered for bot commands.",
        ephemeral=True
    )

# -------- Error handler --------
@setup.error
async def setup_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need to be an **administrator** to use this command.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ An error occurred:\n```{str(error)}```",
            ephemeral=True
        )

# -------- Helper: Channel is registered or not --------
async def is_registered(interaction: discord.Interaction):
    return registered_channels.get(interaction.guild.id) == interaction.channel.id

# -------- /lang --------
@client.tree.command(name="lang", description="Change language")
@app_commands.describe(lang_code="Language code: en or fr")
async def lang(interaction: discord.Interaction, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await interaction.response.send_message("❌ Invalid language. Use 'en' or 'fr'", ephemeral=True)
        return
    user_languages[interaction.user.id] = lang_code
    msg = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await interaction.response.send_message(msg, ephemeral=True)

# -------- /guilds --------
@client.tree.command(name="guilds", description="Show all servers this bot is in")
async def guilds(interaction: discord.Interaction):
    if not client.guilds:
        await interaction.response.send_message("❌ Bot is not in any servers.", ephemeral=True)
        return
    guild_list = "\n".join([f"{i+1}. {g.name}" for i, g in enumerate(client.guilds)])
    await interaction.response.send_message(f"📋 Bot is in the following servers:\n{guild_list}")

# -------- /help --------
@client.tree.command(name="help", description="Show all available bot commands")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "📘 **Available Commands:**\n\n"
        "**/setup** — Register this channel for bot commands\n"
        "**/likesetup** — Activate like command in this channel\n"
        "**/lang [en|fr]** — Set your preferred language\n"
        "**/guilds** — Show all servers the bot is in\n"
        "**/like [uid] [region]** — Add like to Free Fire UID\n"
        "**/check [uid]** — Check ban status of a Free Fire ID\n"
        "**/info [uid]** — Get detailed player info by UID\n"
        "**/help** — Show this help message"
    )

    embed = discord.Embed(
        title="📖 Help Menu",
        description=help_text,
        color=discord.Color.green()
    )
    embed.set_footer(text="📌 Dev </> GAMER SABBIR")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# -------- /like --------
from discord import app_commands
from discord.app_commands import Choice

@client.tree.command(name="like", description="Send like to Free Fire UID")
@app_commands.describe(
    uid="Enter Free Fire UID",
    region="Choose your server region"
)
@app_commands.choices(region=[
    Choice(name="🇧🇩 Bangladesh", value="BD"),
    Choice(name="🇮🇳 India", value="IND"),
    Choice(name="🇵🇰 Pakistan", value="PK")
])
async def like(interaction: discord.Interaction, uid: str, region: str):
    import aiohttp

    # ✅ likesetup চেক
    if interaction.channel.id not in like_enabled_channels:
        await interaction.response.send_message("❌ এই চ্যানেলে `/likesetup` চালানো হয়নি। প্রথমে সেটআপ করুন।", ephemeral=True)
        return

    if not uid.isdigit():
        await interaction.response.send_message("❌ Invalid UID! Example: `/like 123456789`", ephemeral=True)
        return

    await interaction.response.defer()

    url = f"https://jamilikebotapi.vercel.app/like?uid={uid}&server_name={region}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ API returned bad status: {resp.status}")
                    return

                data = await resp.json()

                status = data.get("status")
                nickname = data.get("PlayerNickname")
                uid = data.get("UID")
                likes_before = data.get("LikesbeforeCommand")
                likes_added = data.get("LikesGivenByAPI")
                likes_after = data.get("LikesafterCommand")

                if status == 1:
                    # ✅ Like success embed
                    info = (
                        f"```┌ FREE FIRE LIKE ADDED\n"
                        f"├─ Nickname: {nickname}\n"
                        f"├─ Likes Before: {likes_before}\n"
                        f"├─ Likes Added: {likes_added}\n"
                        f"└─ Likes After: {likes_after}\n"
                        f"UID: {uid}```"
                    )
                    embed = discord.Embed(
                        title="✅ Free Fire Like Added!",
                        description=info,
                        color=discord.Color.purple()
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    embed.set_image(url="https://i.imgur.com/ajygBes.gif")
                    embed.set_footer(text="📌 Dev </> GAMER SABBIR")
                    await interaction.followup.send(embed=embed)
                    return

                elif status == 2:
                    # ⚠️ Max likes reached embed
                    embed = discord.Embed(
                        title="⚠️ No new likes were added",
                        description=(
                            "**MAX LIKES REACHED TODAY**\n\n"
                            "This UID has already received the maximum likes today.\n\n"
                            f"**Nickname:** `{nickname}`\n"
                            f"**UID:** `{uid}`\n"
                            f"**Likes:** `{likes_after}`"
                        ),
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    embed.set_footer(text="📌 Dev </> GAMER SABBIR")
                    await interaction.followup.send(embed=embed)
                    return

                else:
                    await interaction.followup.send("⚠️ Unexpected response. Please try again later.")

    except Exception as e:
        short_error = str(e)
        if len(short_error) > 1900:
            short_error = short_error[:1900] + "..."
        await interaction.followup.send(f"❌ Error:\n```{short_error}```", ephemeral=True)

# -------- /check --------
@client.tree.command(name="check", description="Check Free Fire ID ban status")
@app_commands.describe(uid="Enter Free Fire UID")
async def check_ban_cmd(interaction: discord.Interaction, uid: str):
    import aiohttp

    # 🔐 চ্যানেল রেজিস্টার চেক
    if not await is_registered(interaction):
        guild_id = interaction.guild.id
        reg_channel_id = registered_channels.get(guild_id)
        reg_channel_mention = f"<#{reg_channel_id}>" if reg_channel_id else "`/setup`"

        await interaction.response.send_message(
            f"❌ এই চ্যানেল রেজিস্টার করা হয়নি। অনুগ্রহ করে {reg_channel_mention} তে কমান্ডটি ব্যবহার করুন।",
            ephemeral=True
        )
        return

    if not uid.isdigit():
        await interaction.response.send_message("❌ Invalid UID! উদাহরণ: `/check 123456789`", ephemeral=True)
        return

    await interaction.response.defer()

    url = f"https://api-check-ban.vercel.app/check_ban/{uid}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Could not connect to the API.")
                    return
                data = await resp.json()

        if data.get("status") != 200:
            await interaction.followup.send("❌ No data found or invalid UID.")
            return

        d = data.get("data", {})
        is_banned = int(d.get("is_banned", 0))
        period = d.get("period", "N/A")
        nickname = d.get("nickname", "NA")
        region = d.get("region", "N/A")

        period_str = f"more than {period} months" if isinstance(period, int) else "unavailable"

        if is_banned:
            title = "**▌ Banned Account 🛑**"
            desc = (
                f"{interaction.user.mention}, here is your Free Fire ID ban status:\n"
                f"```┌ Reason: This account was confirmed for using cheats.\n"
                f"├ Suspension duration: {period_str}\n"
                f"├ Nickname: {nickname}\n"
                f"├ Player ID: {uid}\n"
                f"└ Region: {region}```"
            )
            color = 0xFF0000
            image = "https://i.imgur.com/6PDA32M.gif"
        else:
            title = "**▌ Clean Account ✅**"
            desc = (
                f"{interaction.user.mention}, here is your Free Fire ID ban status:\n"
                f"```┌ Status: No evidence of cheat usage.\n"
                f"├ Nickname: {nickname}\n"
                f"├ Player ID: {uid}\n"
                f"└ Region: {region}```"
            )
            color = 0x00FF00
            image = "https://i.imgur.com/166jkZ7.gif"

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url=image)
        embed.set_footer(text="📌 Dev </> GAMER SABBIR")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        error_text = str(e)
        if "1015" in error_text or "rate limit" in error_text.lower():
            msg = (
                "🚫 **Rate Limit Detected:** You've been temporarily blocked by the server due to too many requests.\n"
                "Please wait a few minutes and try again."
            )
        else:
            msg = f"❌ Error occurred:\n```{error_text[:1800]}...```" if len(error_text) > 1800 else f"❌ Error occurred:\n```{error_text}```"

        error_embed = discord.Embed(
            title="❌ Error",
            description=msg,
            color=discord.Color.red()
        )
        try:
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.channel.send(embed=error_embed)



# -------- /info --------
@client.tree.command(name="info", description="Get detailed player info by UID")
@app_commands.describe(uid="Enter Free Fire UID")
async def playerinfo(interaction: discord.Interaction, uid: str):
    import aiohttp
    from datetime import datetime

    def convert_time(timestamp):
        return datetime.utcfromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")

    def safe_block(text: str, limit=950) -> str:
        return text[:limit] + "..." if len(text) > limit else text

    if not await is_registered(interaction):
        guild_id = interaction.guild.id
        reg_channel_id = registered_channels.get(guild_id)
        if reg_channel_id:
            reg_channel_mention = f"<#{reg_channel_id}>"
            await interaction.response.send_message(
                f"❌ এই চ্যানেল রেজিস্টার করা হয়নি। অনুগ্রহ করে / কমান্ডটি {reg_channel_mention} চ্যানেলে ব্যবহার করুন।",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ এই সার্ভারে কোনো চ্যানেল রেজিস্টার করা হয়নি। প্রথমে কোনো একটি চ্যানেলে /setup কমান্ড চালান।",
                ephemeral=True
            )
        return

    if not uid.isdigit():
        await interaction.response.send_message("❌ ভুল UID! উদাহরণ: /info 123456789", ephemeral=True)
        return

    await interaction.response.defer()

    url = f"https://glob-info.vercel.app/info?uid={uid}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await interaction.followup.send("❌ Failed to fetch data. Try again later.", ephemeral=True)
                    return
                data = await response.json()

                if "detail" in data:
                    await interaction.followup.send(f"❌ {data['detail']}", ephemeral=True)
                    return

                info = data["basicInfo"]
                pet = data.get("petInfo", {})
                clan = data.get("clanBasicInfo", {})
                captain = data.get("captainBasicInfo", {})
                social = data.get("socialInfo", {})

                embed = discord.Embed(
                    title=f"📘 Player Profile — {info['nickname']}",
                    description=f"{interaction.user.mention}, here is the player information:",
                    color=discord.Color.random()
                )

                embed.set_thumbnail(
                    url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
                )
                embed.set_image(url=f"https://genprofile.vercel.app/generate?uid={uid}")

                embed.add_field(
                    name="**👤 Player Info**",
                    value=safe_block(
                        f"```┌ Name: {info['nickname']}\n"
                        f"├ UID: {info['accountId']}\n"
                        f"├ Level: {info['level']} (Exp: {info['exp']})\n"
                        f"├ Region: {info['region']}\n"
                        f"├ Likes: {info['liked']}\n"
                        f"├ Honor Score: {data['creditScoreInfo']['creditScore']}\n"
                        f"└ Signature: {social.get('signature', 'N/A')}```"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="**🎮 Player Activity**",
                    value=safe_block(
                        f"```┌ OB Version: {info['releaseVersion']}\n"
                        f"├ BR Rank: {info['rankingPoints']}\n"
                        f"├ CS Points: 0\n"
                        f"├ Created: {convert_time(info['createAt'])}\n"
                        f"└ Last Login: {convert_time(info['lastLoginAt'])}```"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="**🐾 Pet Info**",
                    value=safe_block(
                        f"```┌ Name: {pet.get('name', 'N/A')}\n"
                        f"├ Level: {pet.get('level', 'N/A')}\n"
                        f"└ Exp: {pet.get('exp', 'N/A')}```"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="**🏰 Guild Info**",
                    value=safe_block(
                        f"```┌ Name: {clan.get('clanName', 'N/A')}\n"
                        f"├ ID: {clan.get('clanId', 'N/A')}\n"
                        f"├ Level: {clan.get('clanLevel', 'N/A')}\n"
                        f"└ Members: {clan.get('memberNum', 'N/A')}```"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="**👑 Guild Leader**",
                    value=safe_block(
                        f"```┌ Name: {captain.get('nickname', 'N/A')}\n"
                        f"├ Level: {captain.get('level', 'N/A')}\n"
                        f"├ UID: {captain.get('accountId', 'N/A')}\n"
                        f"├ Likes: {captain.get('liked', 'N/A')}\n"
                        f"├ BR Points: {captain.get('rankingPoints', 'N/A')}\n"
                        f"└ Last Login: {convert_time(captain.get('lastLoginAt', '0'))}```"
                    ),
                    inline=False
                )

                embed.set_footer(text="📌 Dev </> GAMER SABBIR")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            error_text = str(e)
            if "1015" in error_text or "rate limit" in error_text.lower():
                msg = (
                    "🚫 **Rate Limit Detected:** You've been temporarily blocked by the server due to too many requests.\n"
                    "Please wait a few minutes and try again."
                )
            else:
                msg = f"❌ Error occurred:\n```{error_text[:1800]}...```" if len(error_text) > 1800 else f"❌ Error occurred:\n```{error_text}```"
            try:
                await interaction.followup.send(msg, ephemeral=True)
            except discord.errors.HTTPException:
                await interaction.channel.send(msg)




async def main():
    await asyncio.sleep(5)  # ৫ সেকেন্ড দেরি
    await client.start(TOKEN)

asyncio.run(main())
