import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render 무료 플랜 포트 감지용 가짜 서버
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), lambda *args: BaseHTTPRequestHandler(*args))
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()



import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 공백을 제거한 텍스트로 비교
    content = message.content.replace(" ", "")

    if content == "!단미":
        await message.channel.send("한번만 더 건들이면 내가 누군지 똑똑히 알려주겠어")
        return

    elif content == "!채채":
        await message.channel.send('" 채채는 똑똑이야 "')
        return

    elif content == "!유솔":
        await message.channel.send("없어졌다 나타났다 다시 없어질게요 아니 다시 나타날게요")
        return

    elif content == "!이루":
        await message.channel.send(
            "“ 이루 라는 귀족의 이름을 입에 올렸으니 <@1236893502491856946> 에게 1천원 입급 부탁드립나다 ”"
        )
        return

    elif content == "!명온":
        await message.channel.send("며농님,, 오늘도,, 아주 고우심니다,,")
        return

    elif content == "!걸틱":
        await message.channel.send("왜요?")
        return

    elif content == "!이븐":
        await message.channel.send("전 포도주스로 따지면 고농축 엑기스같은 존재죠")
        return

    elif content == "!이스터에그":
        await message.channel.send(
            "쓸대없는 tmi지만 이 봇은 두 번째 희망 봇 이에요. 전에 시도하다가 망했거든요 ㅎ "
        )
        return

    import asyncio
import json
import os
import discord
from discord import app_commands
from discord.ext import commands
from rank_card import create_rank_card

# --------------------------------------------------
# 1. 봇 기본 설정
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "levels.json"
cooldowns = {}


# --------------------------------------------------
# 2. 데이터 관리 및 경험치 공식 함수
# --------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "blacklisted_channels": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# 레벨별 필요 XP 계산 공식 (레벨^2 * 100)
def get_required_xp(level):
    return (level ** 2) * 100


# 특정 레벨까지의 누적 총 필요 XP 계산
def get_total_xp_for_level(level):
    total = 0
    for lvl in range(1, level):
        total += get_required_xp(lvl)
    return total


def add_xp(user_id, amount):
    data = load_data()
    user_str = str(user_id)

    if "users" not in data:
        data["users"] = {}

    if user_str not in data["users"]:
        data["users"][user_str] = {"xp": 0, "level": 1}

    data["users"][user_str]["xp"] += amount

    current_xp = data["users"][user_str]["xp"]
    current_lvl = data["users"][user_str]["level"]
    required_xp = get_required_xp(current_lvl)

    # 레벨업 체크
    while current_xp >= required_xp:
        current_xp -= required_xp
        current_lvl += 1
        required_xp = get_required_xp(current_lvl)

    data["users"][user_str]["xp"] = current_xp
    data["users"][user_str]["level"] = current_lvl

    save_data(data)


# --------------------------------------------------
# 3. 봇 시작 이벤트
# --------------------------------------------------
@bot.event
async def on_ready():
    print(f"로그인 성공: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"동기화 에러: {e}")

    bot.loop.create_task(voice_xp_loop())


# --------------------------------------------------
# 4. 슬래시 명령어 (/제외채널)
# --------------------------------------------------
@bot.tree.command(
    name="제외채널",
    description="경험치가 오르지 않을 채널을 추가하거나 제거합니다.",
)
@app_commands.describe(
    channel="경험치 획득을 막거나 해제할 텍스트/음성 채널 선택"
)
async def exclude_channel(
    interaction: discord.Interaction, channel: discord.abc.GuildChannel
):
    data = load_data()
    blacklisted = data.get("blacklisted_channels", [])

    if channel.id in blacklisted:
        blacklisted.remove(channel.id)
        data["blacklisted_channels"] = blacklisted
        save_data(data)
        await interaction.response.send_message(
            f"✅ {channel.mention} 채널이 제외 목록에서 삭제되었습니다. (경험치 획득 가능)",
            ephemeral=True,
        )
    else:
        blacklisted.append(channel.id)
        data["blacklisted_channels"] = blacklisted
        save_data(data)
        await interaction.response.send_message(
            f"🚫 {channel.mention} 채널이 제외 목록에 추가되었습니다. (경험치 획득 불가)",
            ephemeral=True,
        )


# --------------------------------------------------
# 5. 채팅 경험치 이벤트 (채팅 2번당 10 XP -> 1번당 5 XP)
# --------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    blacklisted_channels = data.get("blacklisted_channels", [])

    # 제외 채널이 아닌 경우
    if message.channel.id not in blacklisted_channels:
        user_id = message.author.id
        now = asyncio.get_event_loop().time()

        # 1분 쿨다운 체크 후 채팅 1회당 5 XP 지급 (2회 = 10 XP)
        if user_id not in cooldowns or now - cooldowns[user_id] > 60:
            cooldowns[user_id] = now
            add_xp(user_id, 5)

    # !랭크 명령어 처리
    content = message.content
    if content == "!랭크" or content == "!rank":
        users_data = data.get("users", {})
        user_info = users_data.get(
            str(message.author.id), {"xp": 0, "level": 1}
        )
        lvl = user_info["level"]
        xp = user_info["xp"]
        max_xp = get_required_xp(lvl)

        # 스타일 1: 전체 누적 총 XP 계산
        total_xp = get_total_xp_for_level(lvl) + xp

        img_buffer = await create_rank_card(
            username=message.author.name,
            avatar_url=message.author.display_avatar.url,
            level=lvl,
            current_xp=xp,
            max_xp=max_xp,
            total_xp=total_xp,
        )
        await message.channel.send(
            file=discord.File(fp=img_buffer, filename="rank.png")
        )
        return

    await bot.process_commands(message)


# --------------------------------------------------
# 6. 음성 통화 경험치 루프 (1시간당 30 XP -> 2분당 1 XP)
# --------------------------------------------------
async def voice_xp_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(120)  # 2분마다 체크

        data = load_data()
        blacklisted_channels = data.get("blacklisted_channels", [])

        for guild in bot.guilds:
            for vc in guild.voice_channels:
                if vc.id not in blacklisted_channels:
                    for member in vc.members:
                        if not member.bot:
                            add_xp(member.id, 1)  # 2분당 1 XP 지급 (1시간 = 30 XP)

    # 다른 command 명령어들도 정상 작동하도록 처리 (주석 # 추가) 
    await bot.process_commands(message)



# Render에 등록할 환경 변수에서 토큰을 안전하게 불러옵니다
bot.run(os.environ["BOT_TOKEN"])
