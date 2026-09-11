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

    # 다른 command 명령어들도 정상 작동하도록 처리 (주석 # 추가) 
    await bot.process_commands(message)



# Render에 등록할 환경 변수에서 토큰을 안전하게 불러옵니다
bot.run(os.environ["BOT_TOKEN"])
