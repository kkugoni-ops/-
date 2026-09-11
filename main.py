import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading

import discord
from discord import app_commands
from discord.ext import commands


# ==================================================
# 1. Render 웹 서버
# ==================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        return


def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


threading.Thread(
    target=run_web_server,
    daemon=True
).start()


# ==================================================
# 2. 봇 설정
# ==================================================

intents = discord.Intents.default()

# !랭크 같은 명령어를 읽기 위해 필요
intents.message_content = True

# 음성 채널 상태 확인
intents.voice_states = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


DATA_FILE = "levels.json"

# 채팅 XP 쿨타임
chat_cooldowns = {}


# ==================================================
# 3. 데이터 불러오기
# ==================================================

def load_data():

    if not os.path.exists(DATA_FILE):

        return {
            "users": {},
            "blacklisted_channels": []
        }

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except Exception as e:

        print(f"[데이터 로드 오류] {e}")

        return {
            "users": {},
            "blacklisted_channels": []
        }


    data.setdefault(
        "users",
        {}
    )

    data.setdefault(
        "blacklisted_channels",
        []
    )


    # ----------------------------------------------
    # 기존 데이터 구조 자동 변환
    # ----------------------------------------------

    for user_id, user in data["users"].items():

        # 예전 xp / level 구조
        if "chat_xp" not in user:

            old_xp = user.get(
                "xp",
                0
            )

            old_level = user.get(
                "level",
                1
            )

            user["chat_xp"] = old_xp
            user["chat_level"] = old_level

            user["chat_total_xp"] = (
                get_total_xp_for_level(old_level)
                + old_xp
            )

            user["voice_xp"] = 0
            user["voice_level"] = 1
            user["voice_total_xp"] = 0

            user.pop(
                "xp",
                None
            )

            user.pop(
                "level",
                None
            )


        # ------------------------------------------
        # 누락된 값 방지
        # ------------------------------------------

        user.setdefault(
            "chat_xp",
            0
        )

        user.setdefault(
            "chat_level",
            1
        )

        user.setdefault(
            "chat_total_xp",
            0
        )

        user.setdefault(
            "voice_xp",
            0
        )

        user.setdefault(
            "voice_level",
            1
        )

        user.setdefault(
            "voice_total_xp",
            0
        )


    return data


# ==================================================
# 4. 데이터 저장
# ==================================================

def save_data(data):

    try:

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

    except Exception as e:

        print(f"[데이터 저장 오류] {e}")


# ==================================================
# 5. XP 계산
# ==================================================

def get_required_xp(level):

    return (
        level ** 2
    ) * 100


def get_total_xp_for_level(level):

    total = 0

    for lvl in range(
        1,
        level
    ):

        total += get_required_xp(
            lvl
        )

    return total


# ==================================================
# 6. 유저 데이터 가져오기
# ==================================================

def get_user_data(user_id):

    data = load_data()

    user_id = str(
        user_id
    )


    if user_id not in data["users"]:

        data["users"][user_id] = {

            "chat_xp": 0,
            "chat_level": 1,
            "chat_total_xp": 0,

            "voice_xp": 0,
            "voice_level": 1,
            "voice_total_xp": 0
        }

        save_data(data)


    return (
        data,
        data["users"][user_id]
    )


# ==================================================
# 7. 채팅 XP 추가
# ==================================================

def add_chat_xp(
    user_id,
    amount
):

    data, user = get_user_data(
        user_id
    )


    user["chat_xp"] += amount

    user["chat_total_xp"] += amount


    # 레벨업
    while user["chat_xp"] >= get_required_xp(
        user["chat_level"]
    ):

        user["chat_xp"] -= get_required_xp(
            user["chat_level"]
        )

        user["chat_level"] += 1


    save_data(data)


# ==================================================
# 8. 음성 XP 추가
# ==================================================

def add_voice_xp(
    user_id,
    amount
):

    data, user = get_user_data(
        user_id
    )


    user["voice_xp"] += amount

    user["voice_total_xp"] += amount


    # 레벨업
    while user["voice_xp"] >= get_required_xp(
        user["voice_level"]
    ):

        user["voice_xp"] -= get_required_xp(
            user["voice_level"]
        )

        user["voice_level"] += 1


    save_data(data)


# ==================================================
# 9. 순위 계산
# ==================================================

def get_rankings(
    category
):

    data = load_data()

    users = data.get(
        "users",
        {}
    )


    if category == "chat":

        return sorted(
            users.items(),
            key=lambda item: item[1].get(
                "chat_total_xp",
                0
            ),
            reverse=True
        )


    if category == "voice":

        return sorted(
            users.items(),
            key=lambda item: item[1].get(
                "voice_total_xp",
                0
            ),
            reverse=True
        )


    # 총합
    return sorted(
        users.items(),
        key=lambda item: (
            item[1].get(
                "chat_total_xp",
                0
            )
            +
            item[1].get(
                "voice_total_xp",
                0
            )
        ),
        reverse=True
    )


# ==================================================
# 10. 유저 순위
# ==================================================

def get_user_rank(
    user_id,
    category
):

    rankings = get_rankings(
        category
    )

    user_id = str(
        user_id
    )


    for index, (
        uid,
        user
    ) in enumerate(
        rankings,
        start=1
    ):

        if uid == user_id:

            return index


    return None


# ==================================================
# 11. XP 진행바
# ==================================================

def make_progress_bar(
    current,
    maximum,
    length=15
):

    if maximum <= 0:

        return "□□□□□□□□□□□□□□□"


    ratio = current / maximum

    ratio = max(
        0,
        min(
            ratio,
            1
        )
    )


    filled = int(
        ratio * length
    )

    empty = length - filled


    return (
        "█" * filled
        +
        "░" * empty
    )


# ==================================================
# 12. 유저 이름 가져오기
# ==================================================

async def get_member_name(
    guild,
    user_id
):

    member = guild.get_member(
        int(user_id)
    )


    if member:

        return member.display_name


    try:

        user = await bot.fetch_user(
            int(user_id)
        )

        return user.name

    except Exception:

        return f"알 수 없는 유저 ({user_id})"


# ==================================================
# 13. 랭크 메시지 생성
# ==================================================

def create_rank_embed(
    target_user,
    user_data
):

    chat_level = user_data.get(
        "chat_level",
        1
    )

    chat_xp = user_data.get(
        "chat_xp",
        0
    )

    chat_total_xp = user_data.get(
        "chat_total_xp",
        0
    )


    voice_level = user_data.get(
        "voice_level",
        1
    )

    voice_xp = user_data.get(
        "voice_xp",
        0
    )

    voice_total_xp = user_data.get(
        "voice_total_xp",
        0
    )


    chat_required = get_required_xp(
        chat_level
    )

    voice_required = get_required_xp(
        voice_level
    )


    total_xp = (
        chat_total_xp
        +
        voice_total_xp
    )


    embed = discord.Embed(
        title="🏆 랭크",
        description=(
            f"## {target_user.display_name}\n"
            f"총 XP **{total_xp:,} XP**"
        ),
        color=discord.Color.blurple()
    )


    # ----------------------------------------------
    # 채팅
    # ----------------------------------------------

    chat_bar = make_progress_bar(
        chat_xp,
        chat_required
    )

    chat_rank = get_user_rank(
        target_user.id,
        "chat"
    )


    embed.add_field(
        name="💬 채팅",
        value=(
            f"레벨 **{chat_level}**\n"
            f"`{chat_bar}`\n"
            f"**{chat_xp:,} / {chat_required:,} XP**\n"
            f"전체 순위 **{chat_rank or '-'}위**\n"
            f"총 획득 XP **{chat_total_xp:,}**"
        ),
        inline=False
    )


    # ----------------------------------------------
    # 음성
    # ----------------------------------------------

    voice_bar = make_progress_bar(
        voice_xp,
        voice_required
    )

    voice_rank = get_user_rank(
        target_user.id,
        "voice"
    )


    embed.add_field(
        name="🎧 음성",
        value=(
            f"레벨 **{voice_level}**\n"
            f"`{voice_bar}`\n"
            f"**{voice_xp:,} / {voice_required:,} XP**\n"
            f"전체 순위 **{voice_rank or '-'}위**\n"
            f"총 획득 XP **{voice_total_xp:,}**"
        ),
        inline=False
    )


    # ----------------------------------------------
    # 총합 순위
    # ----------------------------------------------

    total_rank = get_user_rank(
        target_user.id,
        "total"
    )


    embed.add_field(
        name="🏅 총합",
        value=(
            f"총 XP **{total_xp:,}**\n"
            f"총합 순위 **{total_rank or '-'}위**"
        ),
        inline=False
    )


    embed.set_thumbnail(
        url=target_user.display_avatar.url
    )


    embed.set_footer(
        text="채팅 XP: 1분마다 최대 1회 • 음성 XP: 2분마다"
    )


    return embed


# ==================================================
# 14. 랭크 보내기
# ==================================================

async def send_rank(
    interaction_or_channel,
    target_user
):

    data, user_data = get_user_data(
        target_user.id
    )


    embed = create_rank_embed(
        target_user,
        user_data
    )


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
# 15. 봇 준비
# ==================================================

@bot.event
async def on_ready():

    print(
        f"로그인 성공: {bot.user} "
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
            f"[슬래시 명령어 동기화 오류] {e}"
        )


    # 음성 XP 루프 중복 실행 방지
    if not hasattr(
        bot,
        "voice_task_started"
    ):

        bot.voice_task_started = True

        bot.loop.create_task(
            voice_xp_loop()
        )


# ==================================================
# 16. /제외채널
# ==================================================

@bot.tree.command(
    name="제외채널",
    description="경험치를 막거나 다시 허용할 채널을 설정합니다."
)
@app_commands.describe(
    channel="제외할 채널"
)
async def exclude_channel(
    interaction: discord.Interaction,
    channel: discord.abc.GuildChannel
):

    # 서버 관리자만 사용
    if not interaction.user.guild_permissions.manage_guild:

        await interaction.response.send_message(
            "❌ 서버 관리 권한이 필요합니다.",
            ephemeral=True
        )

        return


    data = load_data()

    blacklisted = data.get(
        "blacklisted_channels",
        []
    )


    if channel.id in blacklisted:

        blacklisted.remove(
            channel.id
        )

        message = (
            f"✅ {channel.mention} "
            "채널의 XP 제한을 해제했습니다."
        )

    else:

        blacklisted.append(
            channel.id
        )

        message = (
            f"🚫 {channel.mention} "
            "채널에서 XP가 오르지 않도록 설정했습니다."
        )


    data["blacklisted_channels"] = blacklisted

    save_data(data)


    await interaction.response.send_message(
        message,
        ephemeral=True
    )


# ==================================================
# 17. /랭크
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

    target = (
        user
        or interaction.user
    )


    await send_rank(
        interaction,
        target
    )


# ==================================================
# 18. /rank
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

    target = (
        user
        or interaction.user
    )


    await send_rank(
        interaction,
        target
    )


# ==================================================
# 19. 순위 보내기
# ==================================================

async def send_rankings(
    interaction_or_channel,
    category
):

    rankings = get_rankings(
        category
    )


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

        embed.description = (
            "아직 XP를 얻은 유저가 없습니다."
        )

    else:

        lines = []


        for index, (
            user_id,
            user_data
        ) in enumerate(
            rankings[:10],
            start=1
        ):

            name = await get_member_name(
                interaction_or_channel.guild,
                user_id
            )


            chat_total = user_data.get(
                "chat_total_xp",
                0
            )

            voice_total = user_data.get(
                "voice_total_xp",
                0
            )


            if category == "chat":

                xp = chat_total

            elif category == "voice":

                xp = voice_total

            else:

                xp = (
                    chat_total
                    +
                    voice_total
                )


            if index == 1:

                medal = "🥇"

            elif index == 2:

                medal = "🥈"

            elif index == 3:

                medal = "🥉"

            else:

                medal = f"`{index}위`"


            lines.append(
                f"{medal} **{name}** — `{xp:,} XP`"
            )


        embed.description = (
            "\n".join(lines)
        )


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
# 20. /랭크순위
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
# 21. /ranklist
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
# 22. 메시지 처리
# ==================================================

@bot.event
async def on_message(message):

    # 봇 무시
    if message.author.bot:
        return


    # ----------------------------------------------
    # 제외 채널
    # ----------------------------------------------

    data = load_data()

    blacklisted_channels = data.get(
        "blacklisted_channels",
        []
    )


    is_blacklisted = (
        message.channel.id
        in blacklisted_channels
    )


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
            f"[{message.author.name}] 랭크 요청"
        )

        await send_rank(
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
    # 제외 채널이면 XP만 차단
    # ----------------------------------------------

    if is_blacklisted:

        await bot.process_commands(
            message
        )

        return


    # ----------------------------------------------
    # 채팅 XP
    # ----------------------------------------------

    user_id = message.author.id

    now = asyncio.get_event_loop().time()


    if (
        user_id not in chat_cooldowns
        or
        now - chat_cooldowns[user_id] >= 60
    ):

        chat_cooldowns[user_id] = now

        add_chat_xp(
            user_id,
            5
        )


    await bot.process_commands(
        message
    )


# ==================================================
# 23. 음성 XP
# ==================================================

async def voice_xp_loop():

    await bot.wait_until_ready()


    while not bot.is_closed():

        # 2분마다
        await asyncio.sleep(
            120
        )


        data = load_data()

        blacklisted_channels = data.get(
            "blacklisted_channels",
            []
        )


        for guild in bot.guilds:

            for voice_channel in guild.voice_channels:

                # 제외된 음성 채널
                if voice_channel.id in blacklisted_channels:

                    continue


                for member in voice_channel.members:

                    # 봇 제외
                    if member.bot:

                        continue


                    add_voice_xp(
                        member.id,
                        1
                    )


# ==================================================
# 24. 봇 실행
# ==================================================

token = os.environ.get(
    "BOT_TOKEN"
)


if not token:

    raise ValueError(
        "BOT_TOKEN 환경 변수가 설정되어 있지 않습니다."
    )


bot.run(
    token
)
