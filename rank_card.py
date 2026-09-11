from PIL import Image, ImageDraw, ImageFont
import os


BACKGROUND_FILE = "rank_background.png"


# ==================================================
# 폰트
# ==================================================

def get_font(size, bold=False):

    font_paths = [

        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]

    for path in font_paths:

        if os.path.exists(path):

            return ImageFont.truetype(
                path,
                size
            )

    return ImageFont.load_default()


# ==================================================
# 랭크 카드 생성
# ==================================================

def create_rank_card(
    username,

    chat_level,
    chat_xp,
    chat_max_xp,
    chat_total_xp,

    voice_level,
    voice_xp,
    voice_max_xp,
    voice_total_xp,

    chat_rank,
    voice_rank,
    total_rank,

    avatar_path=None
):

    width = 1000
    height = 600

    # ----------------------------------------------
    # 배경
    # ----------------------------------------------

    if os.path.exists(
        BACKGROUND_FILE
    ):

        background = Image.open(
            BACKGROUND_FILE
        ).convert("RGB")

        background = background.resize(
            (width, height)
        )

    else:

        background = Image.new(
            "RGB",
            (width, height),
            (30, 30, 30)
        )

    # ----------------------------------------------
    # 반투명 패널
    # ----------------------------------------------

    overlay = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    overlay_draw = ImageDraw.Draw(
        overlay
    )

    overlay_draw.rounded_rectangle(
        (25, 25, width - 25, height - 25),
        radius=30,
        fill=(0, 0, 0, 150)
    )

    background = Image.alpha_composite(
        background.convert("RGBA"),
        overlay
    )

    draw = ImageDraw.Draw(
        background
    )

    # ----------------------------------------------
    # 폰트
    # ----------------------------------------------

    title_font = get_font(
        42,
        True
    )

    username_font = get_font(
        38,
        True
    )

    level_font = get_font(
        28,
        True
    )

    normal_font = get_font(
        23
    )

    small_font = get_font(
        20
    )

    # ----------------------------------------------
    # 아바타
    # ----------------------------------------------

    avatar_size = 150

    avatar_x = 55
    avatar_y = 55

    if (
        avatar_path
        and
        os.path.exists(avatar_path)
    ):

        try:

            avatar = Image.open(
                avatar_path
            ).convert("RGBA")

            avatar = avatar.resize(
                (
                    avatar_size,
                    avatar_size
                )
            )

            mask = Image.new(
                "L",
                (
                    avatar_size,
                    avatar_size
                ),
                0
            )

            mask_draw = ImageDraw.Draw(
                mask
            )

            mask_draw.ellipse(
                (
                    0,
                    0,
                    avatar_size,
                    avatar_size
                ),
                fill=255
            )

            background.paste(
                avatar,
                (
                    avatar_x,
                    avatar_y
                ),
                mask
            )

        except Exception as e:

            print(
                f"[아바타 오류] {e}"
            )

    # ----------------------------------------------
    # 이름
    # ----------------------------------------------

    draw.text(
        (240, 60),
        username,
        font=username_font,
        fill="white"
    )

    # ----------------------------------------------
    # 총 순위
    # ----------------------------------------------

    total_rank_text = (
        f"🏆 전체 순위  "
        f"{total_rank if total_rank else '-'}위"
    )

    draw.text(
        (240, 115),
        total_rank_text,
        font=normal_font,
        fill="white"
    )

    # ----------------------------------------------
    # 채팅 영역
    # ----------------------------------------------

    draw.rounded_rectangle(
        (50, 235, 475, 420),
        radius=20,
        fill=(0, 0, 0, 100)
    )

    draw.text(
        (75, 255),
        "💬 채팅",
        font=title_font,
        fill="white"
    )

    draw.text(
        (75, 310),
        f"LEVEL {chat_level}",
        font=level_font,
        fill="white"
    )

    draw.text(
        (75, 350),
        f"{chat_xp:,} / {chat_max_xp:,} XP",
        font=normal_font,
        fill="white"
    )

    draw.text(
        (75, 385),
        f"순위: {chat_rank if chat_rank else '-'}위",
        font=small_font,
        fill="white"
    )

    # ----------------------------------------------
    # 채팅 XP 바
    # ----------------------------------------------

    chat_bar_x = 520
    chat_bar_y = 310
    chat_bar_width = 400
    chat_bar_height = 30

    draw.rounded_rectangle(
        (
            chat_bar_x,
            chat_bar_y,
            chat_bar_x + chat_bar_width,
            chat_bar_y + chat_bar_height
        ),
        radius=15,
        fill=(70, 70, 70)
    )

    if chat_max_xp > 0:

        chat_progress = min(
            chat_xp / chat_max_xp,
            1
        )

    else:

        chat_progress = 0

    chat_progress_width = int(
        chat_bar_width * chat_progress
    )

    if chat_progress_width > 0:

        draw.rounded_rectangle(
            (
                chat_bar_x,
                chat_bar_y,
                chat_bar_x + chat_progress_width,
                chat_bar_y + chat_bar_height
            ),
            radius=15,
            fill="white"
        )

    # ----------------------------------------------
    # 음성 영역
    # ----------------------------------------------

    draw.rounded_rectangle(
        (50, 440, 475, 575),
        radius=20,
        fill=(0, 0, 0, 100)
    )

    draw.text(
        (75, 455),
        "🎧 음성",
        font=title_font,
        fill="white"
    )

    draw.text(
        (75, 505),
        f"LEVEL {voice_level}",
        font=level_font,
        fill="white"
    )

    draw.text(
        (75, 545),
        f"순위: {voice_rank if voice_rank else '-'}위",
        font=small_font,
        fill="white"
    )

    # ----------------------------------------------
    # 음성 XP
    # ----------------------------------------------

    draw.text(
        (520, 445),
        f"{voice_xp:,} / {voice_max_xp:,} XP",
        font=normal_font,
        fill="white"
    )

    voice_bar_x = 520
    voice_bar_y = 490
    voice_bar_width = 400
    voice_bar_height = 30

    draw.rounded_rectangle(
        (
            voice_bar_x,
            voice_bar_y,
            voice_bar_x + voice_bar_width,
            voice_bar_y + voice_bar_height
        ),
        radius=15,
        fill=(70, 70, 70)
    )

    if voice_max_xp > 0:

        voice_progress = min(
            voice_xp / voice_max_xp,
            1
        )

    else:

        voice_progress = 0

    voice_progress_width = int(
        voice_bar_width * voice_progress
    )

    if voice_progress_width > 0:

        draw.rounded_rectangle(
            (
                voice_bar_x,
                voice_bar_y,
                voice_bar_x + voice_progress_width,
                voice_bar_y + voice_bar_height
            ),
            radius=15,
            fill="white"
        )

    # ----------------------------------------------
    # 총 XP
    # ----------------------------------------------

    total_xp = (
        chat_total_xp
        +
        voice_total_xp
    )

    draw.text(
        (520, 535),
        f"총 XP  {total_xp:,}",
        font=normal_font,
        fill="white"
    )

    # ----------------------------------------------
    # 저장
    # ----------------------------------------------

    output_file = "rank_card.png"

    background.convert(
        "RGB"
    ).save(
        output_file
    )

    return output_file
