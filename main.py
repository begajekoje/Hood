import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("TOKEN")
PRIJAVA_CHANNEL_ID = int(os.getenv("PRIJAVA_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)

# -- async main() funkcija --
async def main():
    # Učitaj sve cogs
    from Prijave import prijava_bot
    prijava_bot.setup(bot)

    await bot.load_extension("XoGame.igra_bot")

    await bot.start(TOKEN)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ Ova komanda je dozvoljena samo administratorima.")
        return  # Zaustavi dalje slanje greške

    elif isinstance(error, commands.CommandNotFound):
        return  # Ne radi ništa ako komanda ne postoji

    else:
        await ctx.send(f"⚠️ Došlo je do greške: {str(error)}")


# -- pokretanje bota --
if __name__ == "__main__":
    asyncio.run(main())
