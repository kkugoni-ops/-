import io
import os
import discord
from discord.ext import commands
from easy_pil import Editor, Canvas, Font, LoadImage

# ... (상단 가짜 서버 및 intents 설정) ...

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command(name="랭크", aliases=["rank", "프로필"])
async def rank_card(ctx):
    user = ctx.author

    # 1. 배경 및 프로필 이미지 로드
    background = Canvas((500, 150), color="#23272A")
    editor = Editor(background)

    # 유저 아바타 이미지 불러오기
    avatar_url = user.display_avatar.url
    profile_image = await LoadImage().async_open(avatar_url)
    profile = Editor(profile_image).resize((100, 100)).circle_image()

    # 2. 이미지에 요소 배치
    editor.paste(profile, (25, 25))  # 프로필 사진 붙이기

    # 3. 텍스트 및 경험치 바 그리기
    # 폰트 설정 (기본 폰트 사용)
    font_large = Font.poppins(size=22, variant="bold")
    font_small = Font.poppins(size=15, variant="regular")

    editor.text((140, 35), str(user.name), font=font_large, color="#FFFFFF")
    editor.text(
        (140, 65),
        "Level 1 | XP: 50 / 100",
        font=font_small,
        color="#AAAAAA",
    )

    # 경험치 바 (게이지)
    editor.rectangle((140, 95), width=330, height=15, fill="#484B4E", radius=10)
    editor.bar(
        (140, 95),
        max_value=100,
        current_value=50,
        width=330,
        height=15,
        fill="#5865F2",
        radius=10,
    )

    # 4. 디스코드 전송용 바이너리 파일로 변환
    file_bytes = editor.to_bytes()
    discord_file = discord.File(
        fp=io.BytesIO(file_bytes), filename="rank.png"
    )

    await ctx.send(file=discord_file)


# ... (기존 on_message 및 bot.run) ...
