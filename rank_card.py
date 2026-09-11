import io
import aiohttp
from easy_pil import Editor, Canvas, Font, load_image


async def create_rank_card(
    username, avatar_url, level=1, current_xp=50, max_xp=100, total_xp=50
):
    # 1. 배경 Canvas 생성 (500x150)
    background = Canvas((500, 150), color="#23272A")
    editor = Editor(background)

    # 2. 유저 아바타 이미지 비동기(Async) 다운로드
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    avatar_data = await response.read()
                    profile_image = load_image(io.BytesIO(avatar_data))
                else:
                    # 이미지 로드 실패 시 기본 캔버스 사용
                    profile_image = Canvas((100, 100), color="#7289DA")
    except Exception as e:
        print(f"아바타 이미지 로드 에러: {e}")
        profile_image = Canvas((100, 100), color="#7289DA")

    # 3. 아바타 서클 변환 및 배치
    profile = Editor(profile_image).resize((100, 100)).circle_image()
    editor.paste(profile, (25, 25))

    # 4. 폰트 설정
    font_large = Font.poppins(size=22, variant="bold")
    font_small = Font.poppins(size=13, variant="regular")

    # 5. 텍스트 표시
    editor.text((140, 28), str(username), font=font_large, color="#FFFFFF")
    editor.text(
        (140, 60),
        f"Level {level}  |  {current_xp} / {max_xp} XP  (Total: {total_xp} XP)",
        font=font_small,
        color="#AAAAAA",
    )

    # 6. 경험치 프로그래스 바 그리기
    editor.rectangle((140, 95), width=330, height=15, fill="#484B4E", radius=10)
    
    # current_xp가 max_xp보다 클 경우 바가 튀어나가는 현상 방지
    display_xp = min(current_xp, max_xp)
    
    editor.bar(
        (140, 95),
        max_value=max_xp,
        current_value=display_xp,
        width=330,
        height=15,
        fill="#5865F2",
        radius=10,
    )

    # 7. 결과 반환 (BytesIO 랭크 카드 파일)
    file_bytes = editor.to_bytes()
    return io.BytesIO(file_bytes)
