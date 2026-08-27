# Importing libraries and modules
import os
import sqlite3
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from instagrapi import Client
from datetime import datetime, timezone
import asyncio
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
DB_PATH = "insta_subscriptions.db"
POLL_SEC = 86400  # Check daily (24 hours)
MAX_FETCH = 1

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS subscriptions (
    guild_id INTEGER,
    channel_id INTEGER,
    ig_user TEXT,
    last_pk INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, ig_user)
    )"""
)
con.commit()

def add_sub(guild_id: int, channel_id: int, ig_user: str):
    cur.execute(
        " INSERT OR REPLACE INTO subscriptions (guild_id, channel_id, ig_user, last_pk)"
        " VALUES (?, ?, ?, COALESCE((SELECT last_pk FROM subscriptions "
        " WHERE guild_id=? AND ig_user=?), 0))",
        (guild_id, channel_id, ig_user.lower(), guild_id, ig_user.lower()),)
    con.commit()

def remove_sub(guild_id: int, ig_user: str):
    cur.execute(
        "DELETE FROM subscriptions WHERE guild_id=? AND ig_user=?",
        (guild_id, ig_user.lower()),)
    deleted = cur.rowcount
    con.commit()
    return deleted > 0

def list_subs(guild_id: int):
    cur.execute(
        "SELECT ig_user FROM subscriptions WHERE guild_id=? ORDER BY ig_user",
        (guild_id,),)
    return [row[0] for row in cur.fetchall()]
    
def get_all_subs():
    cur.execute(
        "SELECT guild_id, channel_id, ig_user, last_pk FROM subscriptions")
    return cur.fetchall()

def update_last_pk(guild_id: int, ig_user: str, new_pk: int):
    cur.execute(
        "UPDATE subscriptions SET last_pk=? WHERE guild_id=? AND ig_user=?",
        (new_pk, guild_id, ig_user.lower()),)
    con.commit()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree 

ig_client = Client()

try:
    ig_client.load_settings("ig_sessions.json")
    ig_client.login(IG_USERNAME, IG_PASSWORD)
except Exception as e:
    ig_client = Client()
    ig_client.login(IG_USERNAME, IG_PASSWORD)
    ig_client.dump_settings("ig_sessions.json")


def create_media_embeds(media):
    caption = getattr(media, "caption_text", None) or "(No caption)"
    post_url = f"https://www.instagram.com/p/{media.code}/"

    embeds = []

    if media.media_type == 8 and hasattr(media, "resources"):
        # For carousel posts, send only one embed with the first image
        em = discord.Embed(description=caption, timestamp=datetime.now(timezone.utc))
        em.set_image(url=media.resources[0].thumbnail_url)
        em.add_field(name="Instagram", value=f"{post_url} (Carousel - {len(media.resources)} images)", inline=False)
        embeds.append(em)
        return embeds

    em = discord.Embed(description=caption, timestamp=datetime.now(timezone.utc))
    em.set_image(url=media.thumbnail_url)
    if media.media_type == 2:
        em.add_field(name="Video", value="(Video - open on instagram)", inline=False)
    em.add_field(name="Instagram", value=post_url, inline=False)
    embeds.append(em)
    return embeds

@tree.command(name="insta_last", description="Fetch last N posts from a public IG user")
@app_commands.describe(username="Instagram username", amount="Number of posts")
async def insta_last(inter: discord.Interaction, username: str, amount: int):
    await inter.response.defer(thinking=True)
    try:
        uid = ig_client.user_id_from_username(username)
        user_info = ig_client.user_info(uid)
        if user_info.is_private:
            await inter.followup.send("This account is private.")
            return
        medias = ig_client.user_medias(uid, amount)
    except Exception as exc:
        await inter.followup.send(f"Error: {exc}")
        return
    
    for m in medias:
        for em in create_media_embeds(m):
            await inter.followup.send(embed=em)


@tree.command(name="insta_search", description="Search recent hashtag posts")
@app_commands.describe(query="#hashtag or keyword", amount="Number of posts")
async def insta_search(inter: discord.Interaction, query: str, amount: int):
    await inter.response.defer(thinking=True)
    try:
        medias = ig_client.hashtag_medias_recent(query.lstrip("#"), amount)
    except Exception as exc:
        await inter.followup.send(f"Error: {exc}")
        return
    
    if not medias:
        await inter.followup.send("No results.")
        return
    
    for m in medias:
        for em in create_media_embeds(m):
            await inter.followup.send(embed=em)

@tree.command(name="insta_sub", description="Subscribed to this channel to an IG account")
@app_commands.describe(username="Instagram username to follow")
async def insta_sub(inter: discord.Interaction, username: str):
    add_sub(inter.guild.id, inter.channel.id, username)
    await inter.response.send_message(f"Subscribe to **{username}** in this channel.")

@tree.command(name="insta_unsub", description="Remove IG subscription from this channel to an IG account")
@app_commands.describe(username="Instagram username to follow")
async def insta_unsub(inter: discord.Interaction, username: str):
    removed = remove_sub(inter.guild.id, username)
    msg = "Unsubscribed." if removed else "Nothing to remove."
    await inter.response.send_message(msg)

@tree.command(name="insta_list", description="List IG accounts followed in this guild")
async def insta_list(inter: discord.Interaction):
    await inter.response.defer(thinking=True)
    subs = list_subs(inter.guild.id)
    if not subs:
        await inter.followup.send("No subscriptions.")
    else:
        await inter.followup.send(
            "**current subscriptions:**\n" + "\n".join(f"- {u}" for u in subs)
        )


@tasks.loop(seconds=POLL_SEC)
async def poll_instagram():
    rows = get_all_subs()
    random.shuffle(rows)

    for guild_id, channel_id, ig_user, last_pk in rows:
        try:
            uid = ig_client.user_id_from_username(ig_user)
        except Exception as exc:
            if 'login_required' in str(exc):
                print(f"Login required for {ig_user}, attempting re-login...")
                try:
                    ig_client.login(IG_USERNAME, IG_PASSWORD)
                    ig_client.dump_settings("ig_sessions.json")
                    uid = ig_client.user_id_from_username(ig_user)
                except Exception as e:
                    print(f"Re-login failed for {ig_user}: {e}")
                    continue
            else:
                print(f"Error getting user ID for {ig_user}: {exc}")
                continue

        try:
            user_info = ig_client.user_info(uid)
            if user_info.is_private:
                print(f"Skipping private account {ig_user}")
                continue
        except Exception as exc:
            print(f"Error getting user info for {ig_user}: {exc}")
            continue

        all_media = []
        try:
            medias = ig_client.user_medias(uid, MAX_FETCH)
            all_media.extend(medias)
        except Exception as exc:
            # Skip this user if medias fail
            continue

        try:
            clips = ig_client.user_clips(uid, MAX_FETCH)
            all_media.extend(clips)
        except Exception as exc:
            print(f"Error fetching clips for {ig_user}: {exc}")
            # Continue without clips

        # Deduplicate all_media by pk to prevent duplicate pings
        all_media = list({m.pk: m for m in all_media}.values())

        if not all_media:
            continue

        new_posts = [m for m in all_media if m.pk > last_pk]
        if not new_posts:
            continue

        new_posts.sort(key=lambda m: m.pk, reverse=True)  # Sort latest first

        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        channel = guild.get_channel(channel_id)
        if not channel:
            continue

        for m in reversed(new_posts):  # Send oldest first
            if getattr(m, 'product_type', None) == 'clips':
                try:
                    await channel.send("🎥 New reel posted! @everyone")
                except discord.HTTPException as exc:
                    print(f"Error sending reel message: {exc}")
            for em in create_media_embeds(m):
                try:
                    await channel.send(embed=em)
                except discord.HTTPException as exc:
                    print(f"Error sending embed: {exc}")
                    break

        update_last_pk(guild_id, ig_user, new_posts[0].pk)  # Update with latest pk
        await asyncio.sleep(random.uniform(1, 3))


@bot.event
async def on_ready():
    await tree.sync()
    if not poll_instagram.is_running():
        poll_instagram.start()

bot.run(TOKEN)