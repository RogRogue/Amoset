import discord 
from discord.ext import commands 
import requests 
from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("HATA: Discord token bulunamadı! .env dosyasını kontrol edin.")
    exit(1)

HENRIK_API_KEY = os.getenv('HENRIK_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix='!', 
    intents=intents, 
    help_command=None,
    application_id='1320088725417627758'
)

GAME_MODES = {
    'competitive': 'Rekabetçi',
    'unrated': 'Derecesiz',
    'swiftplay': 'Tam Gaz'
}

class GameModeSelect(discord.ui.Select):
    def __init__(self, callback):
        options = [
            discord.SelectOption(label=mode_tr, value=mode_en)
            for mode_en, mode_tr in GAME_MODES.items()
        ]
        super().__init__(placeholder='Oyun Modu Seçin...', options=options)
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.values[0])

class MatchPaginationView(discord.ui.View):
    def __init__(self, matches, nickname, tag, mode):
        super().__init__(timeout=60)
        self.matches = matches[:5]
        self.current_page = 0
        self.nickname = nickname
        self.tag = tag
        self.mode = mode

    def create_embed(self):
        match = self.matches[self.current_page]
        embed = discord.Embed(
            description=f"**{GAME_MODES[self.mode]}** Maçları • Sayfa {self.current_page + 1}/{len(self.matches)}",
            color=0xFD4556
        )

        embed.set_author(
            name=f"{self.nickname}#{self.tag}",
            icon_url="https://img.icons8.com/color/512/valorant.png"
        )

        try:
            for player in match['players']['all_players']:
                if player['name'].lower() == self.nickname.lower() and player['tag'].lower() == self.tag.lower():
                    team = player['team'].lower()
                    won = match['teams'][team]['has_won']
                    match_result = "✅ Kazandı" if won else "❌ Kaybetti"
                    match_score = f"{match['teams']['blue']['rounds_won']}-{match['teams']['red']['rounds_won']}"
                    
                    kda = player['stats']
                    kda_ratio = round((kda['kills'] + kda['assists']) / max(kda['deaths'], 1), 2)
                    
                    # Harita bilgisi
                    embed.add_field(
                        name="",
                        value=f"```🗺️ {match['metadata']['map']}```",
                        inline=False
                    )
                    
                    # Skor ve sonuç
                    result_color = "yaml" if won else "fix"
                    embed.add_field(
                        name="",
                        value=f"```{result_color}\n{match_result} • {match_score}```",
                        inline=False
                    )
                    
                    # KDA ve Ajan bilgisi
                    embed.add_field(
                        name="",
                        value=f"```ml\n🎯 K/D/A: {kda['kills']}/{kda['deaths']}/{kda['assists']} (KDA: {kda_ratio})```",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="",
                        value=f"```ml\n🦸 Ajan: {player['character']}```",
                        inline=False
                    )

                    if 'assets' in player and 'agent' in player['assets']:
                        embed.set_thumbnail(url=player['assets']['agent']['small'])
                    
                    embed.set_footer(text="🕒 Sayfa değiştirmek için butonları kullanın.")
                    break

        except Exception as e:
            print(f"Embed oluşturma hatası: {e}")

        return embed

    @discord.ui.button(label="", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.matches) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

class ModeSelectionView(discord.ui.View):
    def __init__(self, nickname, tag):
        super().__init__(timeout=60)
        self.nickname = nickname
        self.tag = tag
        self.author_id = None
        self.add_item(GameModeSelect(self.mode_selected))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir.", ephemeral=True)
            return False
        return True

    async def mode_selected(self, interaction: discord.Interaction, mode: str):
        await interaction.response.defer()
        status_message = await interaction.followup.send("🔍 Maçlar aranıyor...")

        try:
            matches_response = requests.get(
                f'https://api.henrikdev.xyz/valorant/v3/matches/eu/{self.nickname}/{self.tag}',
                headers={
                    'Authorization': HENRIK_API_KEY,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            matches_data = matches_response.json()
            filtered_matches = [
                match for match in matches_data.get('data', [])
                if match.get('metadata', {}).get('mode', '').lower() == mode
            ]

            if not filtered_matches:
                await status_message.delete()
                await interaction.followup.send(f"❌ {GAME_MODES[mode]} maç geçmişi bulunamadı.")
                return

            view = MatchPaginationView(filtered_matches, self.nickname, self.tag, mode)
            await status_message.delete()
            await interaction.followup.send(embed=view.create_embed(), view=view)

        except Exception as e:
            await status_message.delete()
            await interaction.followup.send("❌ Bir hata oluştu.")
            print(f"Hata: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/help"
        )
    )

@bot.tree.command(name="valorant", description="Valorant oyuncusunun son maçlarını gösterir")
@discord.app_commands.describe(
    nickname_tag="Oyuncunun nickname#TAG formatında ismi. Örnek: Oyuncu#TR1"
)
async def valorant_slash(interaction: discord.Interaction, nickname_tag: str):
    if '#' not in nickname_tag:
        await interaction.response.send_message("❌ Lütfen nickname#tag formatında giriniz. Örnek: Oyuncu#TAG", ephemeral=True)
        return
        
    nickname, tag = nickname_tag.split('#')
    nickname = nickname.strip()
    tag = tag.strip()

    try:
        await interaction.response.defer(ephemeral=True)
        status_message = await interaction.followup.send("🔍 Oyuncu aranıyor...", ephemeral=True)
        
        response = requests.get(
            f'https://api.henrikdev.xyz/valorant/v3/matches/eu/{nickname}/{tag}',
            headers={
                'Authorization': HENRIK_API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        if response.status_code != 200:
            await status_message.delete()
            await interaction.followup.send("❌ Oyuncu bulunamadı.", ephemeral=True)
            return

        await status_message.delete()
        view = ModeSelectionView(nickname, tag)
        view.author_id = interaction.user.id
        await interaction.followup.send("Lütfen oyun modunu seçin:", view=view, ephemeral=True)

    except Exception as e:
        if 'status_message' in locals():
            await status_message.delete()
        await interaction.followup.send("❌ Bir hata oluştu.", ephemeral=True)
        print(f"Hata: {e}")

@bot.tree.command(name="help", description="Bot komutları hakkında bilgi verir")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Komutları",
        description="Kullanılabilir komutların listesi.",
        color=0xFD4556
    )

    embed.add_field(
        name="/valorant <oyuncu#tag>",
        value="```\nBelirtilen oyuncunun son 5 maçını gösterir.\n\n"
              "Örnek: /valorant Oyuncu#TR1\n\n"
              "• Rekabetçi, Derecesiz ve Tam Gaz modları için maç geçmişi\n"
              "• K/D/A, harita ve skor bilgileri\n"
              "• Ajan bilgisi ve maç sonucu```",
        inline=False
    )

    embed.set_footer(text="❓ Daha fazla bilgi için geliştirici ile iletişime geçin.")
    
    await interaction.response.send_message(embed=embed)

@bot.command()
async def valorant(ctx, *, nickname_with_tag=None):
    if not nickname_with_tag:
        embed = discord.Embed(
            description="```Örnek: !valorant Oyuncu#TR1```",
            color=0xFD4556
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        return
        
    if '#' not in nickname_with_tag:
        await ctx.send("❌ Lütfen nickname#tag formatında giriniz. Örnek: Oyuncu#TAG", ephemeral=True)
        return
        
    nickname, tag = nickname_with_tag.split('#')
    nickname = nickname.strip()
    tag = tag.strip()

    try:
        status_message = await ctx.send("🔍 Oyuncu aranıyor...", ephemeral=True)
        
        response = requests.get(
            f'https://api.henrikdev.xyz/valorant/v3/matches/eu/{nickname}/{tag}',
            headers={
                'Authorization': HENRIK_API_KEY,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        if response.status_code != 200:
            await status_message.delete()
            await ctx.send("❌ Oyuncu bulunamadı.", ephemeral=True)
            return

        await status_message.delete()
        view = ModeSelectionView(nickname, tag)
        view.author_id = ctx.author.id
        await ctx.send("Lütfen oyun modunu seçin:", view=view, ephemeral=True)

    except Exception as e:
        if 'status_message' in locals():
            await status_message.delete()
        await ctx.send("❌ Bir hata oluştu.", ephemeral=True)
        print(f"Hata: {e}")

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title="Bot Komutları",
        description="Kullanılabilir komutların listesi.",
        color=0xFD4556
    )

    embed.add_field(
        name="!valorant <oyuncu#tag>",
        value="```\nBelirtilen oyuncunun son 5 maçını gösterir.\n\n"
              "Örnek: !valorant Oyuncu#TR1\n\n"
              "• Rekabetçi, Derecesiz ve Tam Gaz modları için maç geçmişi\n"
              "• K/D/A, harita ve skor bilgileri\n"
              "• Ajan bilgisi ve maç sonucu```",
        inline=False
    )

    embed.set_footer(text="❓ Daha fazla bilgi için geliştirici ile iletişime geçin.")
    
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN')) 