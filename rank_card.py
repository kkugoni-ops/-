from easy_pil import Editor, Canvas, Font, load_image_async


async def create_rank_card(
    username,
    avatar_url,
    chat_level=1,
    chat_xp=0,
    chat_max_xp=100,
    chat_total_xp=0,
    voice_level=1,
    voice_xp=0,
    voice_max_xp=100,
    voice_total_xp=0,
    chat_rank=None,
    voice_rank=None,
    total_rank=None,
):
    # --------------------------------------------------
    # 1. 배경
    # --------------------------------------------------
    background = Canvas((700, 300), color="#23272A")
    editor = Editor(background)

    # --------------------------------------------------
    # 2. 프로필 이미지
    # --------------------------------------------------
    try:
        profile_image = await load_image_async(str(avatar_url))
        profile = (
            Editor(profile_image)
            .resize((110, 110))
            .circle_image()
        )
        editor.paste(profile, (30, 30))

    except Exception as e:
        print(f"[프로필 이미지 로드 실패] 기본 이미지 사용: {e}")

        default_image = Canvas(
            (110, 110),
            color="#5865F2"
        )

        profile = Editor(default_image).circle_image()
        editor.paste(profile, (30, 30))

    # --------------------------------------------------
    # 3. 폰트
    # --------------------------------------------------
    try:
        font_name = Font.pica(size=24, bold=True)
        font_main = Font.pica(size=16)
        font_small = Font.pica(size=13)
    except Exception:
        font_name = None
        font_main = None
        font_small = None

    # --------------------------------------------------
    # 4. 이름
    # --------------------------------------------------
    editor.text(
        (165, 30),
        str(username),
        font=font_name,
        color="#FFFFFF"
    )

    # --------------------------------------------------
    # 5. 채팅 정보
    # --------------------------------------------------
    editor.text(
        (165, 75),
        f"💬 채팅 Lv.{chat_level}",
        font=font_main,
        color="#FFFFFF"
    )

    editor.text(
        (165, 105),
        f"{chat_xp} / {chat_max_xp} XP",
        font=font_small,
        color="#AAAAAA"
    )

    editor.text(
        (165, 130),
        f"누적 채팅 XP: {chat_total_xp:,}",
        font=font_small,
        color="#AAAAAA"
    )

    # 채팅 XP 바
    editor.rectangle(
        (165, 155),
        width=480,
        height=14,
        fill="#484B4E",
        radius=7
    )

    chat_display_xp = min(chat_xp, chat_max_xp)

    if chat_max_xp > 0 and chat_display_xp > 0:
        editor.bar(
            (165, 155),
            max_value=chat_max_xp,
            current_value=chat_display_xp,
            width=480,
            height=14,
            fill="#5865F2",
            radius=7
        )

    # --------------------------------------------------
    # 6. 음성 정보
    # --------------------------------------------------
    editor.text(
        (165, 190),
        f"🎧 음성 Lv.{voice_level}",
        font=font_main,
        color="#FFFFFF"
    )

    editor.text(
        (165, 220),
        f"{voice_xp} / {voice_max_xp} XP",
        font=font_small,
        color="#AAAAAA"
    )

    editor.text(
        (165, 245),
        f"누적 음성 XP: {voice_total_xp:,}",
        font=font_small,
        color="#AAAAAA"
    )

    # --------------------------------------------------
    # 7. 총합
    # --------------------------------------------------
    total_xp = chat_total_xp + voice_total_xp

    editor.text(
        (500, 30),
        f"TOTAL {total_xp:,}",
        font=font_small,
        color="#FFFFFF"
    )

    # --------------------------------------------------
    # 8. 순위
    # --------------------------------------------------
    if chat_rank is not None:
        editor.text(
            (30, 265),
            f"채팅 #{chat_rank}",
            font=font_small,
            color="#FFFFFF"
        )

    if voice_rank is not None:
        editor.text(
            (180, 265),
            f"음성 #{voice_rank}",
            font=font_small,
            color="#FFFFFF"
        )

    if total_rank is not None:
        editor.text(
            (330, 265),
            f"종합 #{total_rank}",
            font=font_small,
            color="#FFFFFF"
        )

    # --------------------------------------------------
    # 9. PNG 반환
    # --------------------------------------------------
    file_bytes = editor.to_bytes(fmt="PNG")

    buffer = __import__("io").BytesIO(file_bytes)
    buffer.seek(0)

    return buffer
