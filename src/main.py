#!/usr/bin/evn python3
from dotenv import load_dotenv
import os

load_dotenv()

import logging
from datetime import datetime
from time import time

import discord
from discord import app_commands  # Důležitý import pro slash příkazy
from discord.ext import tasks

from config import *
from discord_logger import DiscordLogger
from offers_storage import OffersStorage
from scrapers.rental_offer import RentalOffer
from scrapers_manager import create_scrapers, fetch_latest_offers
from datetime import datetime


print("DISCORD_TOKEN:", os.getenv("DISCORD_TOKEN"))
print("DISCORD_OFFERS_CHANNEL:", os.getenv("DISCORD_OFFERS_CHANNEL"))


def get_current_daytime() -> bool: return datetime.now().hour in range(6, 22)


# Použijeme defaultní intenty bez privilegovaných
intents = discord.Intents.default()
# Nepotřebujeme message_content pro slash příkazy

# Vytvoříme klasického Client a pak přidáme CommandTree pro slash příkazy
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)  # Toto je pro slash příkazy

daytime = get_current_daytime()
interval_time = config.refresh_interval_daytime_minutes if daytime else config.refresh_interval_nighttime_minutes

scrapers = create_scrapers(config.dispositions)

@client.event
async def on_ready():
    global channel, storage

    dev_channel = client.get_channel(config.discord.dev_channel)
    channel = client.get_channel(config.discord.offers_channel)
    storage = OffersStorage(config.found_offers_file)

    if not config.debug:
        discord_error_logger = DiscordLogger(client, dev_channel, logging.ERROR)
        logging.getLogger().addHandler(discord_error_logger)
    else:
        logging.info("Discord logger is inactive in debug mode")

    logging.info("Available scrapers: " + ", ".join([s.name for s in scrapers]))

    logging.info("Fetching latest offers every {} minutes".format(interval_time))
    
    # Registrace slash příkazů na serveru
    await tree.sync()
    logging.info("Slash commands synced")

    process_latest_offers.start()


@tasks.loop(minutes=interval_time)
async def process_latest_offers():
    logging.info("Fetching offers")

    new_offers: list[RentalOffer] = []
    for offer in fetch_latest_offers(scrapers):
        if not storage.contains(offer):
            new_offers.append(offer)

    first_time = storage.first_time
    storage.save_offers(new_offers)

    logging.info("Offers fetched (new: {})".format(len(new_offers)))

    def parse_price(price_str):
        try:
        # Odstranit mezery a Kč, pak převést na int
            return int(str(price_str).replace(" ", "").replace("Kč", ""))
        except (ValueError, AttributeError):
            return 0  # nebo jiná výchozí hodnota

    if not first_time:
        seen_hashes = set()  # ✅ Inicializujte proměnnou PŘED cyklem!

        for offer in new_offers:
            if parse_price(offer.price) >= 16000:
                continue
            # Detekce duplikátů
            is_duplicate = storage.contains(offer) or (offer.unique_hash in seen_hashes)
            seen_hashes.add(offer.unique_hash)  # 🛠️ Nyní již proměnná existuje
            
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extrahovat dispozici z titulku
            import re
            disposition_match = re.search(r'(\d+\+\w+)', offer.title)
            disposition = disposition_match.group(1) if disposition_match else "Neuvedeno"
        
        # Očistit velikost z titulku
            size_match = re.search(r'(\d+)\s*m²', offer.title)
            size = size_match.group(1) if size_match else "Neuvedeno"
        
        # Vytvoření čistého titulku bez dispozice a velikosti
            clean_title = re.sub(r'\d+\+\w+\s*\d+\s*m²', '', offer.title).strip()
        
            embed = discord.Embed(
                title=clean_title if clean_title else offer.title,
                url=offer.link,
                description=f"📍 **{offer.location}**",
                timestamp=datetime.utcnow(),
                color=offer.scraper.color
            )
        
            embed.add_field(name="Dispozice", value=f"**{disposition}** 🏠", inline=True)
            embed.add_field(name="Velikost", value=f"**{size} m²** 📏", inline=True)
            embed.add_field(name="Cena", value=f"**{offer.price} Kč** 💰", inline=True)
            embed.add_field(name="Čas přidání", value=f"**{current_time}** ⏱️", inline=False)
            embed.set_author(name=offer.scraper.name, icon_url=offer.scraper.logo_url)

            # Zobrazit hash a emoji u duplikátů
            short_hash = offer.unique_hash[:8]  # Prvních 8 znaků
            footer_text = f"🆔 {short_hash}"
            if is_duplicate:
                footer_text += " ✅"
            
            embed.set_footer(text=footer_text)
            embed.set_image(url=offer.image_url)
            
            embed.set_image(url=offer.image_url)
            await channel.send(embed=embed)
    else:
        logging.info("No previous offers, first fetch is running silently")

    global daytime, interval_time
    if daytime != get_current_daytime():  # Pokud stary daytime neodpovida novemu

        daytime = not daytime  # Zneguj daytime (podle podminky se zmenil)

        interval_time = config.refresh_interval_daytime_minutes if daytime else config.refresh_interval_nighttime_minutes

        logging.info("Fetching latest offers every {} minutes".format(interval_time))
        process_latest_offers.change_interval(minutes=interval_time)

    await channel.edit(topic="Last update {}".format("<t:{}:R>".format(int(time()))))


#/*async def test_real_estate_embed(channel):
#    # Vytvoření testovacích dat
#    test_offer = {
#        "title": "Pronájem bytu",
#        "link": "https://example.com/byt",
#        "location": "Brno - Žabrdovice",
#        "price": "15700",
#        "image_url": "https://media.discordapp.net/attachments/794898124102959106/1351252634052460777/IMG20250314231618.jpg?ex=67d9b395&is=67d86215&hm=291edb0932e1c92e591cb9767057ad9e87e903321a0d667bfd55a735470ac7aa&=&format=webp&width=658&height=877",
#        "disposition": "2+kk",
#        "size": "57"
#    }
#    
#    # Vytvoření embeddingu
#    embed = discord.Embed(
#        title=test_offer["title"],
#        url=test_offer["link"],
#        description=f"📍 **{test_offer['location']}**",
#        timestamp=datetime.utcnow(),
#        color=discord.Color.blue()
#    )
#    
#    # Přidání polí s emoji
#    embed.add_field(name="Dispozice", value=f"**{test_offer['disposition']}** 🏠", inline=True)
#    embed.add_field(name="Velikost", value=f"**{test_offer['size']} m²** 📏", inline=True)
#    embed.add_field(name="Cena", value=f"**{test_offer['price']} Kč** 💰", inline=True)
#    embed.add_field(name="Čas přidání", value=f"**{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}** ⏱️", inline=False)
#    
#    # Nastavení autora a obrázku
#    embed.set_author(name="TestScraper", icon_url="https://example.com/logo.png")
#    embed.set_image(url=test_offer["image_url"])
#    
#    # Odeslání zprávy
#    await channel.send(embed=embed)
#
#
## Definice slash příkazu pomocí app_commands místo commands
#@tree.command(name="test_embed", description="Testovací příkaz pro zobrazení embeddingu nabídky pronájmu")
#async def test_embed_command(interaction: discord.Interaction):
#    await test_real_estate_embed(interaction.channel)
#    await interaction.response.send_message("Test embed byl odeslán!", ephemeral=True)
#
#
if __name__ == "__main__":
    logging.basicConfig(
        level=(logging.DEBUG if config.debug else logging.INFO),
        format='%(asctime)s - [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug("Running in debug mode")

    client.run(config.discord.token, log_level=logging.INFO)
