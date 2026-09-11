from PIL import Image, ImageDraw, ImageFont
import os


BACKGROUND_FILE = "rank_background.png"


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
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def create_rank_card(
    username,
    level,
    xp,
    required_xp,
    avatar_path=None
):
    width = 900
    height = 300

    # 배경 이미지
    if os.path.exists(BACKGROUND_FILE):
        background = Image.open(BACKGROUND_FILE).convert("RGB")
        background = background.resize((width, height))
    else:
        background = Image.new("RGB", (width, height), (30, 30, 30))

    draw = ImageDraw.Draw(background)

    # 반투명 어두운 영역
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        (20, 20, width - 20, height - 20),
        radius=25,
        fill=(0, 0, 0, 130)
    )

    background = Image.alpha_composite(
        background.convert("RGBA"),
        overlay
    )

    draw = ImageDraw.Draw(background)

    # 폰트
    username_font = get_font(42, True)
    level_font = get_font(30, True)
    normal_font = get_font(24)

    # 아바타
    avatar_size = 150
    avatar_x = 55
    avatar_y = 75

    if avatar_path and os.path.exists(avatar_path):
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size))

        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse(
            (0, 0, avatar_size, avatar_size),
            fill=255
        )

        background.paste(
            avatar,
            (avatar_x, avatar_y),
            mask
        )

    # 이름
    text_x = 240

    draw.text(
        (text_x, 65),
        username,
        font=username_font,
        fill="white"
    )

    # 레벨
    draw.text(
        (text_x, 125),
        f"LEVEL {level}",
        font=level_font,
        fill="white"
    )

    # XP
    draw.text(
        (text_x, 170),
        f"{xp:,} / {required_xp:,} XP",
        font=normal_font,
        fill="white"
    )

    # 경험치 바
    bar_x = text_x
    bar_y = 215
    bar_width = 600
    bar_height = 30

    draw.rounded_rectangle(
        (
            bar_x,
            bar_y,
            bar_x + bar_width,
            bar_y + bar_height
        ),
        radius=15,
        fill=(70, 70, 70)
    )

    if required_xp > 0:
        progress = min(xp / required_xp, 1)
    else:
        progress = 0

    progress_width = int(bar_width * progress)

    if progress_width > 0:
        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + progress_width,
                bar_y + bar_height
            ),
            radius=15,
            fill=(255, 255, 255)
        )

    output_file = "rank_card.png"
    background.convert("RGB").save(output_file)

    return output_file
