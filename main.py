import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading

import discord
from discord import app_commands
from discord.ext import commands

from rank_card import create_rank_card


# ==================================================
# 1. Render 웹 서비스 포트
# ==================================================

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        lambda *args: BaseHTTPRequestHandler(*args)
    )

    server.serve_forever()


threading.Thread(
    target=run_dummy_server,
    daemon=True
).start()


# ==================================================
# 2. 봇 설정
# ==================================================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


DATA_FILE = "levels.json"

chat_cooldowns = {}


# ==================================================
# 3. 데이터
# ==================================================

def load_data():

    if os.path.exists(DATA_FILE):

        try:

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                # --------------------------------------
                # 기존 데이터 자동 변환
                # --------------------------------------

                if "users" in data:

                    for user_id, user in data["users"].items():

                        # 예전 구조
                        if "chat_xp" not in user:

                            old_xp = user.get("xp", 0)
                            old_level = user.get("level", 1)

                            user["chat_xp"] = old_xp
                            user["chat_level"] = old_level

                            user["chat_total_xp"] = (
                                get_total_xp_for_level(old_level)
                                + old_xp
                            )

                            user["voice_xp"] = 0
                            user["voice_level"] = 1
                            user["voice_total_xp"] = 0

                            user.pop("xp", None)
                            user.pop("level", None)

                        # 누락 데이터 방지
                        user.setdefault("chat_xp", 0)
                        user.setdefault("chat_level", 1)
                        user.setdefault("chat_total_xp", 0)

                        user.setdefault("voice_xp", 0)
                        user.setdefault("voice_level", 1)
                        user.setdefault("voice_total_xp", 0)

                data.setdefault("users", {})
                data.setdefault("blacklisted_channels", [])

                return data

        except Exception as e:

            print(f"[데이터 로드 실패] {e}")

    return {
        "users": {},
        "blacklisted_channels": []
    }


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ==================================================
# 4. XP 계산
# ==================================================

def get_required_xp(level):

    return (level ** 2) * 100


def get_total_xp_for_level(level):

    total = 0

    for lvl in range(1, level):
        total += get_required_xp(lvl)

    return total


# ==================================================
# 5. 유저 데이터 가져오기
# ==================================================

def get_user_data(user_id):

    data = load_data()

    user_str = str(user_id)

    if user_str not in data["users"]:

        data["users"][user_str] = {
            "chat_xp": 0,
            "chat_level": 1,
            "chat_total_xp": 0,

            "voice_xp": 0,
            "voice_level": 1,
            "voice_total_xp": 0
        }

        save_data(data)

    user = data["users"][user_str]

    return data, user


# ==================================================
# 6. XP 추가
# ==================================================

def add_chat_xp(user_id, amount):

    data, user = get_user_data(user_id)

    user["chat_xp"] += amount
    user["chat_total_xp"] += amount

    while user["chat_xp"] >= get_required_xp(
        user["chat_level"]
    ):

        user["chat_xp"] -= get_required_xp(
            user["chat_level"]
        )

        user["chat_level"] += 1

    save_data(data)


def add_voice_xp(user_id, amount):

    data, user = get_user_data(user_id)

    user["voice_xp"] += amount
    user["voice_total_xp"] += amount

    while user["voice_xp"] >= get_required_xp(
        user["voice_level"]
    ):

        user["voice_xp"] -= get_required_xp(
            user["voice_level"]
        )

        user["voice_level"] += 1

    save_data(data)


# ==================================================
# 7. 순위 계산
# ==================================================

def get_rankings(category):

    data = load_data()

    users = data.get("users", {})

    if category == "chat":

        key = "chat_total_xp"

    elif category == "voice":

        key = "voice_total_xp"

    else:

        def total_key(item):
            user = item[1]

            return (
                user.get("chat_total_xp", 0)
                + user.get("voice_total_xp", 0)
            )

        return sorted(
            users.items(),
            key=total_key,
            reverse=True
        )

    return sorted(
        users.items(),
        key=lambda item: item[1].get(key, 0),
        reverse=True
    )


def get_user_rank(user_id, category):

    rankings = get_rankings(category)

    user_id = str(user_id)

    for index, (uid, user) in enumerate(
        rankings,
        start=1
    ):

        if uid == user_id:

            return index

    return None


# ==================================================
# 8. 봇 시작
# ==================================================

@bot.event
async def on_ready():

    print(
        f"로그인 성공: {bot.user.name} "
        f"(ID: {bot.user.id})"
    )

    try:

        synced = await bot.tree.sync()

        print(
            f"슬래시 명령어 "
            f"{len(synced)}개 동기화 완료"
        )

    except Exception as e:

        print(
            f"슬래시 명령어 동기화 실패: {e}"
        )

    # 중복 실행 방지
    if not hasattr(bot, "voice_task_started"):

        bot.voice_task_started = True

        bot.loop.create_task(
            voice_xp_loop()
        )


# ==================================================
# 9. 제외 채널
# ==================================================

@bot.tree.command(
    name="제외채널",
    description="경험치가 오르지 않을 채널을 추가하거나 제거합니다."
)
@app_commands.describe(
    channel="경험치를 막거나 해제할 텍스트/음성 채널"
)
async def exclude_channel(
    interaction: discord.Interaction,
    channel: discord.abc.GuildChannel
):

    data = load_data()

    blacklisted = data.get(
        "blacklisted_channels",
        []
    )

    if channel.id in blacklisted:

        blacklisted.remove(channel.id)

        data["blacklisted_channels"] = blacklisted

        save_data(data)

        await interaction.response.send_message(
            f"✅ {channel.mention} 채널이 제외 목록에서 삭제되었습니다.",
            ephemeral=True
        )

    else:

        blacklisted.append(channel.id)

        data["blacklisted_channels"] = blacklisted

        save_data(data)

        await interaction.response.send_message(
            f"🚫 {channel.mention} 채널이 제외 목록에 추가되었습니다.",
            ephemeral=True
        )


# ==================================================
# 10. 랭크 카드
# ==================================================

async def send_rank_card(
    interaction_or_channel,
    target_user
):

    data, user = get_user_data(
        target_user.id
    )

    chat_level = user.get(
        "chat_level",
        1
    )

    chat_xp = user.get(
        "chat_xp",
        0
    )

    chat_total_xp = user.get(
        "chat_total_xp",
        0
    )

    voice_level = user.get(
        "voice_level",
        1
    )

    voice_xp = user.get(
        "voice_xp",
        0
    )

    voice_total_xp = user.get(
        "voice_total_xp",
        0
    )

    chat_max_xp = get_required_xp(
        chat_level
    )

    voice_max_xp = get_required_xp(
        voice_level
    )

    chat_rank = get_user_rank(
        target_user.id,
        "chat"
    )

    voice_rank = get_user_rank(
        target_user.id,
        "voice"
    )

    total_rank = get_user_rank(
        target_user.id,
        "total"
    )

    # Discord 프로필 이미지
    avatar_url = target_user.display_avatar.replace(
        format="png",
        size=256
    ).url

    try:

        image = await create_rank_card(

            username=target_user.name,

            avatar_url=avatar_url,

            chat_level=chat_level,
            chat_xp=chat_xp,
            chat_max_xp=chat_max_xp,
            chat_total_xp=chat_total_xp,

            voice_level=voice_level,
            voice_xp=voice_xp,
            voice_max_xp=voice_max_xp,
            voice_total_xp=voice_total_xp,

            chat_rank=chat_rank,
            voice_rank=voice_rank,
            total_rank=total_rank
        )

        file = discord.File(
            fp=image,
            filename="rank.png"
        )

        if isinstance(
            interaction_or_channel,
            discord.Interaction
        ):

            await interaction_or_channel.response.send_message(
                file=file
            )

        else:

            await interaction_or_channel.send(
                file=file
            )

    except Exception as e:

        print(
            f"[랭크 카드 오류] {e}"
        )

        if isinstance(
            interaction_or_channel,
            discord.Interaction
        ):

            await interaction_or_channel.response.send_message(
                "❌ 랭크 카드를 만드는 중 오류가 발생했습니다."
            )

        else:

            await interaction_or_channel.send(
                "❌ 랭크 카드를 만드는 중 오류가 발생했습니다."
            )


# ==================================================
# 11. /랭크
# ==================================================

@bot.tree.command(
    name="랭크",
    description="내 랭크 또는 다른 사람의 랭크를 확인합니다."
)
@app_commands.describe(
    user="랭크를 확인할 유저"
)
async def rank_slash(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    target = user or interaction.user

    await send_rank_card(
        interaction,
        target
    )


# ==================================================
# 12. /rank
# ==================================================

@bot.tree.command(
    name="rank",
    description="내 랭크 또는 다른 사람의 랭크를 확인합니다."
)
@app_commands.describe(
    user="랭크를 확인할 유저"
)
async def rank_slash_english(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    target = user or interaction.user

    await send_rank_card(
        interaction,
        target
    )


# ==================================================
# 13. 랭크 순위 메시지 생성
# ==================================================

async def send_rankings(
    interaction_or_channel,
    category
):

    rankings = get_rankings(category)

    if category == "chat":

        title = "💬 채팅 XP 순위"

    elif category == "voice":

        title = "🎧 음성 XP 순위"

    else:

        title = "🏆 총합 XP 순위"

    embed = discord.Embed(
        title=title,
        color=discord.Color.blurple()
    )

    if not rankings:

        embed.description = "아직 XP를 얻은 유저가 없습니다."

    else:

        lines = []

        for index, (user_id, user_data) in enumerate(
            rankings[:10],
            start=1
        ):

            try:

                user = interaction_or_channel.guild.get_member(
                    int(user_id)
                )

                name = (
                    user.display_name
                    if user
                    else f"알 수 없는 유저 ({user_id})"
                )

            except Exception:

                name = f"알 수 없는 유저 ({user_id})"

            chat_total = user_data.get(
                "chat_total_xp",
                0
            )

            voice_total = user_data.get(
                "voice_total_xp",
                0
            )

            total = (
                chat_total
                + voice_total
            )

            if category == "chat":

                xp = chat_total

            elif category == "voice":

                xp = voice_total

            else:

                xp = total

            lines.append(
                f"**{index}위**  {name} — `{xp:,} XP`"
            )

        embed.description = "\n".join(lines)

    if isinstance(
        interaction_or_channel,
        discord.Interaction
    ):

        await interaction_or_channel.response.send_message(
            embed=embed
        )

    else:

        await interaction_or_channel.send(
            embed=embed
        )


# ==================================================
# 14. /랭크순위
# ==================================================

@app_commands.choices(
    category=[
        app_commands.Choice(
            name="채팅 XP",
            value="chat"
        ),
        app_commands.Choice(
            name="음성 XP",
            value="voice"
        ),
        app_commands.Choice(
            name="총합 XP",
            value="total"
        )
    ]
)
@bot.tree.command(
    name="랭크순위",
    description="채팅/음성/총합 XP 순위를 확인합니다."
)
async def ranking_slash(
    interaction: discord.Interaction,
    category: app_commands.Choice[str]
):

    await send_rankings(
        interaction,
        category.value
    )


# ==================================================
# 15. /ranklist
# ==================================================

@app_commands.choices(
    category=[
        app_commands.Choice(
            name="채팅 XP",
            value="chat"
        ),
        app_commands.Choice(
            name="음성 XP",
            value="voice"
        ),
        app_commands.Choice(
            name="총합 XP",
            value="total"
        )
    ]
)
@bot.tree.command(
    name="ranklist",
    description="채팅/음성/총합 XP 순위를 확인합니다."
)
async def ranking_slash_english(
    interaction: discord.Interaction,
    category: app_commands.Choice[str]
):

    await send_rankings(
        interaction,
        category.value
    )


# ==================================================
# 16. 채팅 XP
# ==================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    data = load_data()

    blacklisted_channels = data.get(
        "blacklisted_channels",
        []
    )

    if message.channel.id in blacklisted_channels:

        return

    # ----------------------------------------------
    # 기존 커스텀 명령어
    # ----------------------------------------------

    clean_content = (
        message.content
        .replace(" ", "")
    )

    if clean_content == "!단미":

        await message.channel.send(
            "한번만 더 건들이면 내가 누군지 똑똑히 알려주겠어"
        )

        return

    elif clean_content == "!채채":

        await message.channel.send(
            '" 채채는 똑똑이야 "'
        )

        return

    elif clean_content == "!유솔":

        await message.channel.send(
            "없어졌다 나타났다 다시 없어질게요 아니 다시 나타날게요"
        )

        return

    elif clean_content == "!이루":

        await message.channel.send(
            "“ 이루 라는 귀족의 이름을 입에 올렸으니 <@1236893502491856946> 에게 1천원 입급 부탁드립나다 ”"
        )

        return

    elif clean_content == "!명온":

        await message.channel.send(
            "며농님,, 오늘도,, 아주 고우심니다,,"
        )

        return

    elif clean_content == "!걸틱":

        await message.channel.send(
            "왜요?"
        )

        return

    elif clean_content == "!이븐":

        await message.channel.send(
            "전 포도주스로 따지면 고농축 엑기스같은 존재죠"
        )

        return

    elif clean_content == "!이스터에그":

        await message.channel.send(
            "쓸대없는 tmi지만 이 봇은 두 번째 희망 봇 이에요. 전에 시도하다가 망했거든요 ㅎ"
        )

        return

    # ----------------------------------------------
    # !랭크
    # ----------------------------------------------

    cmd_text = (
        message.content
        .strip()
        .lower()
        .replace(" ", "")
    )

    if cmd_text in [
        "!랭크",
        "!rank"
    ]:

        print(
            f"[{message.author.name}] 랭크 카드 요청"
        )

        await send_rank_card(
            message.channel,
            message.author
        )

        return

    # ----------------------------------------------
    # !순위
    # ----------------------------------------------

    if cmd_text in [
        "!순위",
        "!ranklist"
    ]:

        await send_rankings(
            message.channel,
            "total"
        )

        return

    # ----------------------------------------------
    # 채팅 XP
    # ----------------------------------------------

    user_id = message.author.id

    now = asyncio.get_event_loop().time()

    if (
        user_id not in chat_cooldowns
        or now - chat_cooldowns[user_id] > 60
    ):

        chat_cooldowns[user_id] = now

        add_chat_xp(
            user_id,
            5
        )

    await bot.process_commands(message)


# ==================================================
# 17. 음성 XP
# ==================================================

async def voice_xp_loop():

    await bot.wait_until_ready()

    while not bot.is_closed():

        await asyncio.sleep(120)

        data = load_data()

        blacklisted_channels = data.get(
            "blacklisted_channels",
            []
        )

        for guild in bot.guilds:

            for vc in guild.voice_channels:

                if vc.id in blacklisted_channels:
                    continue

                for member in vc.members:

                    if member.bot:
                        continue

                    add_voice_xp(
                        member.id,
                        1
                    )


# ==================================================
# 18. 봇 실행
# ==================================================

token = os.environ.get(
    "BOT_TOKEN"
)

if not token:

    raise ValueError(
        "BOT_TOKEN 환경 변수가 설정되어 있지 않습니다."
    )


bot.run(token)
