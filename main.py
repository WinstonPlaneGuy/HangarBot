import discord
from discord.ext import commands
from discord import app_commands
import json
import re
import random
import logging
from dotenv import load_dotenv
import os
import time
import asyncio

# sets up bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# sets up logging and intents
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Load aircraft data from JSON
with open("dictionary.json", "r", encoding="utf-8") as f:
    aircraft_data = json.load(f)

# build lookup dictionary (with aliases)
lookup = {}

#track last response time per aircraft
last_response_time ={}
COOLDOWN_SECONDS = 30

for name, data in aircraft_data.items():
    lookup[name.lower()] = name
    for alias in data.get("aliases", []):
        lookup[alias.lower()] = name

# Sync bot
@bot.event
async def on_ready():
    await bot.tree.sync() # syncs commands

    print(f"Logged in as {bot.user.name}")

    # sets status
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"Planespotting")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# Responder script
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    # aircraft responder
    for keyword, aircraft_name in lookup.items():
        if re.search(rf"\b{re.escape(keyword)}\b", content):

            # set time and get the last aircraft name
            now = time.time()
            last_time = last_response_time.get(aircraft_name, 0)

            # if still on cooldown, ignore
            if now - last_time < COOLDOWN_SECONDS:
                break

            # update cooldown timer
            last_response_time[aircraft_name] = now

            aircraft_info = aircraft_data[aircraft_name]
            image_path = random.choice(aircraft_info["images"])

            file = discord.File(image_path, filename="aircraft.jpg")

            embed = discord.Embed(title=aircraft_name)
            embed.set_image(url="attachment://aircraft.jpg")

            await message.channel.send(embed=embed, file=file)
            break

    # heart responder
    if message.author == bot.user:
        return

    content = message.content.lower()

    if "thank you hangarbot" in content or "thanks hangarbot" in content:
        try:
            await message.add_reaction("❤️")
        except Exception as e:
            print(f"Failed to react to message: {e}")

    # plaen responder
    if bot.user.mentioned_in(message):
        await message.channel.send(f"plaen")
        return

    await bot.process_commands(message)

# Wiki Search Command

from wikiextractor import get_aircraft_specs

@bot.tree.command(name="search", description="Search aircraft specs from Wikipedia")
@app_commands.describe(
    name="Name of the aircraft (e.g., Tu-28)",
    category="Which category to display"
)
@app_commands.choices(
    category=[
        app_commands.Choice(name="General Characteristics", value="general characteristics"),
        app_commands.Choice(name="Performance", value="performance"),
        app_commands.Choice(name="Armament", value="armament"),
        app_commands.Choice(name="Avionics", value="avionics")
    ]
)
async def search(interaction: discord.Interaction, name: str, category: app_commands.Choice[str]):

    await interaction.response.defer()  # prevent timeout for scraper

    loop = asyncio.get_running_loop()
    try:
        specs = await loop.run_in_executor(None, get_aircraft_specs, name)
    except Exception as e:
        await interaction.followup.send("Failed to retrieve aircraft data.")
        print(e)
        return

    # Only send the selected category
    output = f"=== {specs['title']} ===\n\n"
    selected_items = specs.get(category.value, [])

    output += f"--- {category.value.title()} ---\n"

    if selected_items:
        for item in selected_items:
            output += f"- {item}\n"
    else:
        output += "No data available\n"

    # Discord limit safety
    await interaction.followup.send(output[:2000])

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)