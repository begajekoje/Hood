import discord
from discord.ext import commands, tasks
import random
import json
import os

RANK_FILE = "xo_rank.json"
ROLE_ID = 123456789012345678  # Zamijeni sa stvarnim ID-em role

class XOGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_channel_id = 123456789012345678  # Zamijeni sa stvarnim ID kanala
        self.players = []
        self.turn = 0
        self.board = ["⬜"] * 9
        self.game_active = False
        self.join_message = None
        self.auto_game.start()

        if not os.path.exists(RANK_FILE):
            with open(RANK_FILE, "w") as f:
                json.dump({}, f)

    def cog_unload(self):
        self.auto_game.cancel()

    def make_move(self, index, symbol):
        if self.board[index] == "⬜":
            self.board[index] = symbol
            return True
        return False

    def check_winner(self):
        combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in combos:
            a, b, c = combo
            if self.board[a] == self.board[b] == self.board[c] != "⬜":
                return self.board[a]
        if "⬜" not in self.board:
            return "draw"
        return None

    def update_rank(self, user_id):
        with open(RANK_FILE, "r") as f:
            data = json.load(f)
        data[str(user_id)] = data.get(str(user_id), 0) + 1
        with open(RANK_FILE, "w") as f:
            json.dump(data, f)

    def get_rank(self, user_id):
        with open(RANK_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(user_id), 0)

    def get_top(self):
        with open(RANK_FILE, "r") as f:
            data = json.load(f)
        return sorted(data.items(), key=lambda x: x[1], reverse=True)

    @tasks.loop(hours=1)
    async def auto_game(self):
        if random.random() < 0.5:
            await self.send_game_message()

    @auto_game.before_loop
    async def before_game(self):
        await self.bot.wait_until_ready()

    async def send_game_message(self):
        channel = self.bot.get_channel(self.game_channel_id)
        if channel:
            self.players = []
            self.turn = 0
            self.board = ["⬜"] * 9
            self.game_active = False
            view = XOJoinView(self)
            self.join_message = await channel.send(content="⚔️ **IX OX Igrica!**\nKlikni zeleno dugme da se pridružiš. Prva 2 igrača ulaze!", view=view)

    @commands.command()
    async def startx(self, ctx):
        if ROLE_ID not in [role.id for role in ctx.author.roles]:
            return await ctx.send("⛔ Samo korisnici sa određenom rolom mogu pokrenuti igru.")

        self.players = []
        self.turn = 0
        self.board = ["⬜"] * 9
        self.game_active = False
        view = XOJoinView(self)
        self.join_message = await ctx.send(content="⚔️ **IX OX Igrica!**\nKlikni zeleno dugme da se pridružiš. Prva 2 igrača ulaze!", view=view)

    @commands.command()
    async def rank(self, ctx):
        score = self.get_rank(ctx.author.id)
        await ctx.send(f"📊 {ctx.author.display_name}, tvoj rang: {score} pobjeda.")

    @commands.command()
    async def stopx(self, ctx):
        if ROLE_ID not in [role.id for role in ctx.author.roles]:
            return await ctx.send("⛔ Samo korisnici sa određenom rolom mogu zaustaviti igru.")

        if not self.game_active:
            return await ctx.send("⚠️ Nema aktivne igre za zaustaviti.")

        self.players = []
        self.turn = 0
        self.board = ["⬜"] * 9
        self.game_active = False
        self.join_message = None

        await ctx.send("🛑 Igra je prekinuta od strane admina.")

    @commands.command()
    async def top(self, ctx):
        top_players = self.get_top()[:10]
        if not top_players:
            return await ctx.send("Nema podataka.")
        message = "**🏆 Top 10 igrača:**\n"
        for i, (user_id, score) in enumerate(top_players, 1):
            user = await self.bot.fetch_user(int(user_id))
            message += f"{i}. {user.display_name}: {score} pobjeda\n"
        await ctx.send(message)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetrank(self, ctx):
        with open(RANK_FILE, "w") as f:
            json.dump({}, f)
        await ctx.send("🔁 Rang lista je resetovana!")

class XOJoinView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.join_button = JoinButton(cog)
        self.add_item(self.join_button)

class JoinButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="🎓 Pridruži se", style=discord.ButtonStyle.success, custom_id="join")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if not self.cog.join_message or interaction.message.id != self.cog.join_message.id:
            return await interaction.response.send_message("⚠️ Ne možeš koristiti ovaj dugmić!", ephemeral=True)

        if len(self.cog.players) >= 2:
            return await interaction.response.send_message("⚠️ Igra je već počela!", ephemeral=True)

        if interaction.user in self.cog.players:
            return await interaction.response.send_message("✅ Već si u igri!", ephemeral=True)

        self.cog.players.append(interaction.user)
        await interaction.response.send_message(f"{interaction.user.mention} se pridružio!")

        if len(self.cog.players) == 2:
            await interaction.channel.send(
                f"🌟 Igra počinje između {self.cog.players[0].mention} i {self.cog.players[1].mention}!"
            )

            self.cog.turn = 0
            self.cog.board = ["⬜"] * 9
            self.cog.game_active = True

            view = XOGameView(self.cog)
            if self.cog.join_message:
                await self.cog.join_message.edit(content="🔷 **IX OX Tabla**", view=view)

class XOGameView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        for i in range(9):
            self.add_item(XOButton(index=i, cog=cog))

class XOButton(discord.ui.Button):
    def __init__(self, index, cog):
        super().__init__(label="⬜", style=discord.ButtonStyle.success, row=index // 3, custom_id=f"cell_{index}")
        self.index = index
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if not self.cog.game_active:
            return await interaction.response.send_message("❌ Igra nije aktivna.", ephemeral=True)
        if interaction.user != self.cog.players[self.cog.turn % 2]:
            return await interaction.response.send_message("⏳ Nije tvoj red.", ephemeral=True)

        symbol = "❌" if self.cog.turn % 2 == 0 else "⭕"
        if self.cog.make_move(self.index, symbol):
            self.label = symbol
            self.style = discord.ButtonStyle.danger if symbol == "❌" else discord.ButtonStyle.primary
            self.disabled = True
            self.cog.turn += 1

            winner = self.cog.check_winner()
            if winner:
                self.cog.game_active = False
                if winner == "draw":
                    await interaction.response.edit_message(content="🤝 Neriješeno!", view=self.view)
                else:
                    pobjednik = self.cog.players[0 if winner == "❌" else 1]
                    self.cog.update_rank(pobjednik.id)
                    await interaction.response.edit_message(
                        content=f"🏆 {winner} pobjeđuje! ({pobjednik.mention})",
                        view=self.view
                    )
            else:
                await interaction.response.edit_message(view=self.view)
        else:
            await interaction.response.send_message("⛔ Polje je već zauzeto.", ephemeral=True)

async def setup(bot):
    cog = XOGame(bot)
    await bot.add_cog(cog)
