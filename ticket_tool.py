import discord
from discord.ext import commands
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import datetime
import os

from dotenv import load_dotenv
load_dotenv()

# 🔁 ID-jevi iz .env fajla
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
STAFF_SEF_ROLE_ID = int(os.getenv("STAFF_SEF_ROLE_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))

ticket_counter = 0  # Broj ticketa

# 📄 Generisanje PDF transkripta
async def create_pdf_transcript(channel: discord.TextChannel) -> discord.File:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, y, f"Transcript za kanal: {channel.name}")
    y -= 20
    pdf.drawString(40, y, f"Datum: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 40

    messages = await channel.history(limit=100, oldest_first=True).flatten()
    for msg in messages:
        content = f"[{msg.created_at.strftime('%H:%M')}] {msg.author.name}: {msg.content}"
        lines = pdf.beginText(40, y)
        lines.setFont("Helvetica", 10)
        lines.textLines(content)
        pdf.drawText(lines)
        y -= 40
        if y < 50:
            pdf.showPage()
            y = height - 50

    pdf.drawString(40, 30, f"Generiran od strane Hood Tiket Sistema • {datetime.datetime.utcnow().year}")
    pdf.save()
    buffer.seek(0)
    return discord.File(buffer, filename="transcript.pdf")

# ✅ Modal za potvrdu zatvaranja
class ConfirmCloseModal(discord.ui.Modal, title="Zatvori Tiket?"):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        transcript_file = await create_pdf_transcript(self.channel)

        if log_channel:
            await log_channel.send(
                f"📁 Tiket `{self.channel.name}` zatvoren od strane {interaction.user.mention}",
                file=transcript_file
            )

        await self.channel.send("🗑️ Tiket se zatvara za 5 sekundi...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=5))
        await self.channel.delete()

# 🔘 Dugme za zatvaranje ticketa
class CloseButton(discord.ui.Button):
    def __init__(self, channel):
        super().__init__(label="Zatvori tiket", style=discord.ButtonStyle.danger)
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConfirmCloseModal(self.channel))

# 🎛️ View koji sadrži dugme
class ControlView(discord.ui.View):
    def __init__(self, channel):
        super().__init__()
        self.add_item(CloseButton(channel))

# 🔽 Dropdown meni
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛡️ Staff prijava", value="staff-prijava", description="Prijavi ponašanje Staff člana"),
            discord.SelectOption(label="⚠️ Žalba na Staff člana", value="zalba", description="Uloži žalbu protiv Staff člana"),
            discord.SelectOption(label="🌟 Pohvala na Staff člana", value="pohvala", description="Pohvali korisnika Staff tima"),
            discord.SelectOption(label="💬 Općenito", value="opcenito", description="Postavi pitanje ili traži drugu pomoć"),
        ]
        super().__init__(placeholder="⬇️ Izaberi vrstu tiketa...", options=options)

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("⚠️ Tiket kategorija nije pronađena. Provjeri TICKET_CATEGORY_ID u .env fajlu.", ephemeral=True)
            return

        for kanal in category.channels:
            if interaction.user.name.lower() in kanal.name:
                await interaction.response.send_message("⚠️ Već imaš otvoren tiket!", ephemeral=True)
                return

        ticket_counter += 1
        ticket_number = str(ticket_counter).zfill(3)
        kanal_ime = f"{self.values[0]}-{ticket_number}"

        staff_sef = guild.get_role(STAFF_SEF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }

        if staff_sef:
            overwrites[staff_sef] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_kanal = await guild.create_text_channel(
            kanal_ime, overwrites=overwrites, category=category
        )

        await ticket_kanal.send(
            f"👋 {interaction.user.mention} Dobrodošao/la u svoj tiket!\n**Staff tim** će ti se uskoro javiti.\nZa zatvaranje klikni dugme ispod",
            view=ControlView(ticket_kanal)
        )

        await interaction.response.send_message(
            f"✅ Tiket otvoren: {ticket_kanal.mention}", ephemeral=True
        )

# 📦 Glavni dropdown view
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketSelect())
