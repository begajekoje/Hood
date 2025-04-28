import discord
from discord.ext import commands
import os


def setup(bot):
    @bot.command(name="prijava")
    async def prijava(ctx):
        try:
            await ctx.message.delete()

            embed = discord.Embed(
                title="📄 Prijava kazne – Formular",
                description=(
                    "**Ispuni sljedeće podatke i pošalji kao poruku:**\n\n"
                    "*Discord korisničko ime:*\n"
                    "*Datum i vrijeme izricanja kazne:*\n"
                    "*Vrsta kazne:*\n"
                    "*Razlog kazne:*\n"
                    "*Dokazi:*"
                ),
                color=0x2ecc71
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("⛔ Nemam permisije da izbrišem tvoju komandu ili pošaljem poruku.")

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.channel.id == int(os.getenv("PRIJAVA_CHANNEL_ID")):
            content = message.content

            if all(kljuc in content for kljuc in [
                "Discord korisničko ime:",
                "Datum i vrijeme izricanja kazne:",
                "Vrsta kazne:",
                "Razlog kazne:",
                "Dokazi:"
            ]):
                try:
                    await message.delete()
                except discord.NotFound:
                    pass

                linije = content.splitlines()
                podaci = {}
                for linija in linije:
                    if ":" in linija:
                        kljuc, vrijednost = linija.split(":", 1)
                        podaci[kljuc.strip()] = vrijednost.strip()

                # Tvoji emoji ID-ovi:
                emoji_user = "<:Korisnik:1362341811527618590>"
                emoji_time = "<a:arrow:1341588341358989382>"
                emoji_warn = "<a:arrow:1341588341358989382>"
                emoji_reason = "<a:arrow:1341588341358989382>"
                emoji_proof = "<a:arrow:1341588341358989382>"
                emoji_title = "<:Info:1334186844782465097>"

                embed = discord.Embed(
                    title=f"{emoji_title} Nova prijava!                         ",
                    color=0xff0000
                )
                embed.add_field(name=f"{emoji_user} Discord korisnik", value=podaci.get("Discord korisničko ime", "N/A"), inline=False)
                embed.add_field(name=f"{emoji_time} Datum i vrijeme", value=podaci.get("Datum i vrijeme izricanja kazne", "N/A"), inline=False)
                embed.add_field(name=f"{emoji_warn} Vrsta kazne", value=podaci.get("Vrsta kazne", "N/A"), inline=False)
                embed.add_field(name=f"{emoji_reason} Razlog", value=podaci.get("Razlog kazne", "N/A"), inline=False)
                embed.add_field(name=f"{emoji_proof} Dokazi", value=podaci.get("Dokazi", "N/A"), inline=False)
                embed.set_footer(text=f"Poslao: {message.author}", icon_url=message.author.avatar.url if message.author.avatar else None)

                await message.channel.send(embed=embed)

                log_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
                if log_channel:
                    await log_channel.send(
                        f"*<:Checkmark:1362019058177802363> Prijavu poslao:* {message.author.mention}\n```{content}```"
                    )

        await bot.process_commands(message)