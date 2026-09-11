import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading
import discord
from discord import app_commands
from discord.ext import commands
from rank_card import create_rank_card

# --------------------------------------------------
# 1. Render 웹 서비스 포트 감지용 서버
# --------------------------------------------------
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(
        ("0.0.0.0", port), lambda *args: BaseHTTPRequestHandler(*args)
    )
    server.serve_forever()


threading.Thread(target=run_dummy_server, daemon=True).start()

# --------------------------------------------------
# 2. 봇 기본 설정
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "levels.json"
cooldowns = {}


# --------------------------------------------------
# 3. 데이터 및 레벨 계산 함수
# --------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "blacklisted_channels": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_required_xp(level):
    return (level**2) * 100


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

    while current_xp >= required_xp:
        current_xp -= required_xp
        current_lvl += 1
        required_xp = get_required_xp(current_lvl)

    data["users"][user_str]["xp"] = current_xp
    data["users"][user_str]["level"] = current_lvl

    save_data(data)


# --------------------------------------------------
# 4. 봇 시작 이벤트
# --------------------------------------------------
@bot.event
async def on_ready():
    print(f"로그인 성공: {bot.user.name} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"슬래시 명령어 동기화 실패: {e}")

    bot.loop.create_task(voice_xp_loop())


# --------------------------------------------------
# 5. 슬래시 명령어 (/제외채널)
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
            f"✅ {channel.mention} 채널이 제외 목록에서 삭제되었습니다.",
            ephemeral=True,
        )
    else:
        blacklisted.append(channel.id)
        data["blacklisted_channels"] = blacklisted
        save_data(data)
        await interaction.response.send_message(
            f"🚫 {channel.mention} 채널이 제외 목록에 추가되었습니다.",
            ephemeral=True,
        )


# --------------------------------------------------
# 6. 채팅 이벤트 (커스텀 명령어 + 랭크 카드 + 경험치)
# --------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 제외 채널 감지
    data = load_data()
    blacklisted_channels = data.get("blacklisted_channels", [])
    if message.channel.id in blacklisted_channels:
        return

    # 1) 커스텀 응답 처리
    clean_content = message.content.replace(" ", "")

    if clean_content == "!단미":
        await message.channel.send("한번만 더 건들이면 내가 누군지 똑똑히 알려주겠어")
        return
    elif clean_content == "!채채":
        await message.channel.send('" 채채는 똑똑이야 "')
        return
    elif clean_content == "!유솔":
        await message.channel.send("없어졌다 나타났다 다시 없어질게요 아니 다시 나타날게요")
        return
    elif clean_content == "!이루":
        await message.channel.send(
            "“ 이루 라는 귀족의 이름을 입에 올렸으니 <@1236893502491856946> 에게 1천원 입급 부탁드립나다 ”"
        )
        return
    elif clean_content == "!명온":
        await message.channel.send("며농님,, 오늘도,, 아주 고우심니다,,")
        return
    elif clean_content == "!걸틱":
        await message.channel.send("왜요?")
        return
    elif clean_content == "!이븐":
        await message.channel.send("전 포도주스로 따지면 고농축 엑기스같은 존재죠")
        return
    elif clean_content == "!이스터에그":
        await message.channel.send(
            "쓸대없는 tmi지만 이 봇은 두 번째 희망 봇 이에요. 전에 시도하다가 망했거든요 ㅎ "
        )
        return

    # 2) !랭크 명령어 처리
    cmd_text = message.content.strip().lower().replace(" ", "")
    if cmd_text in ["!랭크", "!rank"]:
        print(f"[{message.author.name}] 랭크 카드 요청 감지됨")
        users_data = data.get("users", {})
        user_info = users_data.get(str(message.author.id), {"xp": 0, "level": 1})
        lvl = user_info.get("level", 1)
        xp = user_info.get("xp", 0)
        max_xp = get_required_xp(lvl)
        total_xp = get_total_xp_for_level(lvl) + xp

        try:
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
            print(f"[{message.author.name}] 랭크 카드 전송 성공!")
        except Exception as e:
            print(f"[오류 발생] 랭크 카드 생성 실패: {e}")
            await message.channel.send("❌ 랭크 카드를 생성하는 중 오류가 발생했습니다.")
        return

    # 3) 일반 채팅 경험치 지급 (1분 쿨다운)
    user_id = message.author.id
    now = asyncio.get_event_loop().time()

    if user_id not in cooldowns or now - cooldowns[user_id] > 60:
        cooldowns[user_id] = now
        add_xp(user_id, 5)

    await bot.process_commands(message)


# --------------------------------------------------
# 7. 음성 채널 경험치 스케줄러 (2분당 1 XP)
# --------------------------------------------------
async def voice_xp_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(120)

        data = load_data()
        blacklisted_channels = data.get("blacklisted_channels", [])

        for guild in bot.guilds:
            for vc in guild.voice_channels:
                if vc.id not in blacklisted_channels:
                    for member in vc.members:
                        if not member.bot:
                            add_xp(member.id, 1)


# 봇 실행
token = os.environ.get("BOT_TOKEN")
if not token:
    raise ValueError("BOT_TOKEN 환경 변수가 설정되어 있지 않습니다.")

bot.run(token)
