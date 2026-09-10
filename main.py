import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user}")


@bot.command()
async def 안녕(ctx):
    await ctx.send("안녕하세요! 24시간 켜져 있는 클라우드 봇입니다.")


# Render에 등록할 환경 변수에서 토큰을 안전하게 불러옵니다
bot.run(os.environ["BOT_TOKEN"])
