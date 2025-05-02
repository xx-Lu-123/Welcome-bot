import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CONFIG_FILE = 'config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@bot.event
async def on_ready():
    print(f'{bot.user} 已上線！')
    try:
        synced = await tree.sync()
        print(f"已全域同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"斜線指令同步失敗：{e}")
    game = discord.Game('努力做出更多指令內容')
    await bot.change_presence(status=discord.Status.idle, activity=game)

@tree.command(name="set", description="設定歡迎或離開訊息")
@app_commands.describe(mode="選擇要設定的訊息類型", message="訊息內容，可用 {user} 代表用戶")
@app_commands.choices(mode=[
    app_commands.Choice(name="歡迎訊息", value="welcome"),
    app_commands.Choice(name="離開訊息", value="leave")
])
async def set_message(interaction: discord.Interaction, mode: app_commands.Choice[str], message: str):
    gid = str(interaction.guild.id)
    config.setdefault(gid, {})[mode.value] = message
    save_config()
    await interaction.response.send_message(f"{mode.name} 已設定為：{message}", ephemeral=True)

@tree.command(name="setchannel", description="設定發送訊息的頻道")
async def setchannel(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    config.setdefault(gid, {})['channel'] = interaction.channel.id
    save_config()
    await interaction.response.send_message("已設定此頻道為訊息發送地點", ephemeral=True)

@tree.command(name="clear", description="清除歡迎或離開訊息")
@app_commands.describe(mode="選擇要清除的訊息類型")
@app_commands.choices(mode=[
    app_commands.Choice(name="歡迎訊息", value="welcome"),
    app_commands.Choice(name="離開訊息", value="leave")
])
async def clear_message(interaction: discord.Interaction, mode: app_commands.Choice[str]):
    gid = str(interaction.guild.id)
    if gid in config and mode.value in config[gid]:
        del config[gid][mode.value]
        save_config()
        await interaction.response.send_message(f"{mode.name} 已清除", ephemeral=True)
    else:
        await interaction.response.send_message(f"尚未設定 {mode.name}", ephemeral=True)

@tree.command(name="setuserphotos", description="設定是否顯示使用者大頭貼於歡迎/離開訊息")
async def setuserphotos(interaction: discord.Interaction):
    class PhotoView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.select(
            placeholder="選擇要設定的訊息類型",
            options=[
                discord.SelectOption(label="歡迎訊息", value="welcome"),
                discord.SelectOption(label="離開訊息", value="leave")
            ]
        )
        async def select_mode(self, interaction2: discord.Interaction, select: discord.ui.Select):
            mode = select.values[0]
            await interaction2.response.send_message(
                f"你想在 **{mode}** 訊息中顯示使用者大頭貼嗎？",
                view=ConfirmPhotoView(mode),
                ephemeral=True
            )

    class ConfirmPhotoView(discord.ui.View):
        def __init__(self, mode):
            super().__init__(timeout=60)
            self.mode = mode

        @discord.ui.button(label="顯示", style=discord.ButtonStyle.success)
        async def enable_photo(self, interaction3: discord.Interaction, button: discord.ui.Button):
            gid = str(interaction.guild.id)
            config.setdefault(gid, {}).setdefault("photo", {})[self.mode] = True
            save_config()
            await interaction3.response.send_message(f"{self.mode} 的大頭貼顯示已啟用！", ephemeral=True)

        @discord.ui.button(label="不顯示", style=discord.ButtonStyle.danger)
        async def disable_photo(self, interaction3: discord.Interaction, button: discord.ui.Button):
            gid = str(interaction.guild.id)
            config.setdefault(gid, {}).setdefault("photo", {})[self.mode] = False
            save_config()
            await interaction3.response.send_message(f"{self.mode} 的大頭貼顯示已停用！", ephemeral=True)

    await interaction.response.send_message("請選擇要設定的訊息類型：", view=PhotoView(), ephemeral=True)

@tree.command(name="welcomehelp", description="顯示歡迎指令說明")
async def welcomehelp(interaction: discord.Interaction):
    embed = discord.Embed(
        title=" 歡迎使用歡迎Cat機器人（≧∇≦）",
        description=(
            "**⭐️ 指令說明：**\n"
            "1. `/set` 設定歡迎 / 離開 訊息\n"
            "2. `/setchannel` 設定發送頻道\n"
            "3. `/clear` 清除歡迎 / 離開 訊息\n"
            "4. `/setuserphotos` 設定是否顯示使用者大頭貼\n"
            "5. `/welcomehelp` 查看此幫助訊息\n"
            "6. `{user}` 可提及使用者\n\n"
            "**📝更新日誌：**\n"
            "1. 新增指令`/setuserphotos`可變更是否截取使用者頭像\n"
            "2. 新增`24`小時在線功能\n"
            "3. 變更`/welcomehelp`指令回覆方式、機器人頭像\n"
            "```機器人版本：v1.3.2\nBot上線狀態：🟢\n伺服器延遲：🟡```\n"
            "如果還有可以改進的地方可以點擊下方按鈕，給予建議\n感謝使用《歡迎Cat》機器人"
        ),
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="📝建議回饋", url="https://forms.gle/CNypXVbL9xT5GdCU9", style=discord.ButtonStyle.link))
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_member_join(member):
    gid = str(member.guild.id)
    if gid in config and 'channel' in config[gid] and 'welcome' in config[gid]:
        channel = bot.get_channel(config[gid]['channel'])
        message = config[gid]['welcome'].replace("{user}", member.mention)
        photo_enabled = config.get(gid, {}).get("photo", {}).get("welcome", False)
        if photo_enabled:
            embed = discord.Embed(description=message, color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        else:
            await channel.send(message)

@bot.event
async def on_member_remove(member):
    gid = str(member.guild.id)
    if gid in config and 'channel' in config[gid] and 'leave' in config[gid]:
        channel = bot.get_channel(config[gid]['channel'])
        message = config[gid]['leave'].replace("{user}", member.mention)
        photo_enabled = config.get(gid, {}).get("photo", {}).get("leave", False)
        if photo_enabled:
            embed = discord.Embed(description=message, color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        else:
            await channel.send(message)
            
bot.run(TOKEN)
