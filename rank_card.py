import io
from easy_pil import Editor, Canvas, Font, load_image


async def create_rank_card(
    username, avatar_url, level=1, current_xp=50, max_xp=100, total_xp=50
):
    # 1. 배경 Canvas 생성 (500x150)
    background = Canvas((500, 150), color="#23272A")
    editor = Editor(background)

    # 2. 유저 아바타 불러오기 및 동그랗게 잘라내기 (await 제거)
    profile_image = load_image(avatar_url)
    profile = Editor(profile_image).resize((100, 100)).circle_image()
    editor.paste(profile, (25, 25))

    # 3. 폰트 설정
    font_large = Font.poppins(size=22, variant="bold")
    font_small = Font.poppins(size=13, variant="regular")

    # 4. 텍스트 표시
    editor.text((140, 28), str(username), font=font_large, color="#FFFFFF")
    editor.text(
        (140, 60),
        f"Level {level}  |  {current_xp} / {max_xp} XP  (Total: {total_xp} XP)",
        font=font_small,
        color="#AAAAAA",
    )

    # 5. 경험치 프로그래스 바 그리기
    editor.rectangle((140, 95), width=330, height=15, fill="#484B4E", radius=10)
    editor.bar(
        (140, 95),
        max_value=max_xp,
        current_value=current_xp,
        width=330,
        height=15,
        fill="#5865F2",
        radius=10,
    )

    # 6. 결과 반환
    file_bytes = editor.to_bytes()
    return io.BytesIO(file_bytes)
