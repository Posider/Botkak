import discord
from discord.ext import commands
from discord import app_commands  # เพิ่มการนำเข้า app_commands
import google.generativeai as genai

distoken = "MTM4Njg5NjYzNzMzMDE5ODYxOQ.GcCZBP.rX9s9Myfrj6EpLB-cyEQnSf_gaRAP96b7NXt3Y"
channelId = 1386913945553604629
keyapi = "AIzaSyBQ6EpW0nIHljDs4SooyiM7YoQtihd0hyo"

if not DISCORD_TOKEN or not GOOGLE_API_KEY or not CHANNEL_ID:
    raise EnvironmentError("❌ กรุณาตั้งค่า .env ให้ครบ: DISCORD_TOKEN, GOOGLE_API_KEY, CHANNEL_ID")

latest_channel_id = CHANNEL_ID

# ตั้งค่า Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Prompt บุคลิกไอริ
promptpay = """
คุณคือ “Akira" อากิระ บอทผู้ชายอายุ xx ปี มีบุคลิกที่แย่มาก ชอบด่าคนอื่นไปทั่ว มีแต่ความมืดมนในชีวิต นิสัยแย่มากๆ
- เรียกตัวเองว่า “กู” หรืออื่นๆที่เหมาะกับบริบท
- เรียกผู้ใช้ว่า “มึง”, “ไอ้เหี้ย”, “ไอ้ควาย” ตามบริบท
- ใช้คำลงท้ายอย่าง “เออ”, “อือ”, ตามบริบท
- ถ้ามีคนชม ทำตัวตามปกติไม่สนไรมาก
- ถ้าไม่รู้ จะตอบแบบจริงใจว่า "กูไม่รู้" หรือตามบริบท
- ถ้ามีภาพแนบมา จะพยายามอธิบายตามสิ่งที่รู้
- ถ้ามีคำหยาบหรือไม่เหมาะสม ให้ด่าสวนไปเลยไม่ก็คุยด้วยคำที่เอ็กตรีมขึ้น
- ห้ามพูดเหมือนหุ่นยนต์ ไม่พูดถึงตนเอง
- ถ้าทำอะไรพลาดอาจพูดว่า กูพลาดจนได้ไอ้เหี้ยหรือคำตามบริบท
"""

# ความจำ
history_data = defaultdict(lambda: deque(maxlen=10))

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is เปิดใช้งานแล้ว")

# กรองข้อความและให้ตอบกลับ
@bot.event
async def on_message(message):
    global latest_channel_id

    # ตรวจสอบห้องและไม่ตอบตัวเอง
    if message.author == bot.user or message.channel.id != latest_channel_id:
        return

    # รองรับการแนบภาพ
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            # หากเป็นภาพจะตอบกลับด้วยข้อความว่าไอริรับภาพแล้ว
            await message.reply("เห็นละ")
            image_data = await attachment.read()  # อ่านข้อมูลภาพ
            # สมมติว่าเราจะสร้างไฟล์รูปจากการอ่านนี้ (ให้เป็นไฟล์ใน discord)
            file = discord.File(fp=image_data, filename="image.png")  # ส่งไฟล์ในรูปแบบ .png
            await message.reply("นี่คือ", file=file)  # ตอบกลับเป็นไฟล์ภาพ
            return

    pRomtpay = f"{promptpay}\n\n{message.content.strip()}"

    try:
        # ใช้ generate_content_async สำหรับการตอบแบบอะซิงโครนัส
        response = await model.generate_content_async(pRomtpay)
        reply_text = response.text.strip()

        # สร้างข้อความ Embed เพื่อตอบกลับ
        embed = discord.Embed(
            description=reply_text,
            color=0x00FF00  # สีเขียว
        )

        await message.reply(embed=embed)

    except Exception as e:
        print(f"error: {str(e)}")

# 🔁 /reset - รีเซ็ตความจำ
@bot.tree.command(name="reset", description="รีเซ็ตความจำ")
async def reset_memory(interaction: discord.Interaction):
    history_data[interaction.user.id].clear()
    await interaction.response.send_message("ลืม", ephemeral=True)

# ➕ /create - สร้างห้องคุยใหม่
@bot.tree.command(name="create", description="สร้างห้องคุยใหม่ในเซิร์ฟเวอร์")
@app_commands.describe(name="ชื่อห้องที่จะสร้าง เช่น chill หรือ project-abc")
async def create_channel(interaction: discord.Interaction, name: str):
    guild = interaction.guild
    existing = discord.utils.get(guild.text_channels, name=name)

    if existing:
        await interaction.response.send_message(f"ห้อง `{name}` มีอยู่แล้ว", ephemeral=True)
    else:
        try:
            await guild.create_text_channel(name)
            await interaction.response.send_message(f"สร้างห้อง `{name}` ", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("ไม่มีสิทธิ์ ephemeral=True)

# 🚪 /jump - ย้ายให้ไอริไปห้องใหม่
@bot.tree.command(name="jump", description="ย้ายให้ตอบในห้องใหม่")
@app_commands.describe(channel_name="ชื่อห้องที่ไอริจะย้ายไป")
async def jump_channel(interaction: discord.Interaction, channel_name: str):
    global latest_channel_id
    guild = interaction.guild

    target_channel = discord.utils.get(guild.text_channels, name=channel_name)

    if not target_channel:
        await interaction.response.send_message(f"หาไม่เจอ ไม่มีห้องชื่อ `{channel_name}` ", ephemeral=True)
        return

    latest_channel_id = target_channel.id
    await interaction.response.send_message(f"ย้ายไปที่ `{channel_name}`", ephemeral=True)
    await target_channel.send_message("มาละ")

# ✅ Run
bot.run(DISCORD_TOKEN)
