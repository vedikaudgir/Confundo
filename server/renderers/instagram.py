from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 2000
PADDING = 64


def _font(path, size):
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                line = candidate
                continue

            if line:
                lines.append(line)
                line = ""

            while draw.textbbox((0, 0), word, font=font)[2] > max_width:
                split_at = max(1, len(word) // 2)
                while split_at > 1 and draw.textbbox(
                    (0, 0), word[:split_at], font=font
                )[2] > max_width:
                    split_at -= 1
                lines.append(word[:split_at])
                word = word[split_at:]
            line = word

        lines.append(line)
    return lines


def _participant_name(participants, participant_id, fallback):
    for participant in participants:
        if participant[0] == participant_id:
            return participant[2] or fallback
    return fallback


def _draw_participant_avatar(img, draw, participant, server_dir, box):
    x1, y1, x2, y2 = box
    size = x2 - x1
    avatar_path = participant[4] if participant and len(participant) > 4 else None
    if avatar_path:
        candidate = Path(avatar_path)
        if not candidate.is_absolute():
            candidate = (server_dir.parent / candidate).resolve()
        if candidate.is_file():
            avatar = Image.open(candidate).convert("RGBA").resize(
                (size, size), Image.Resampling.LANCZOS
            )
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            img.paste(avatar, (x1, y1), mask)
            return

    draw.ellipse(box, fill=(226, 232, 224))
    initial = ((participant[2] if participant else None) or "C").strip()[:1].upper()
    font = _font(server_dir / "static" / "fonts" / "Roboto-Regular.ttf", 31)
    initial_box = draw.textbbox((0, 0), initial, font=font)
    draw.text(
        (
            x1 + size // 2 - (initial_box[2] - initial_box[0]) // 2,
            y1 + size // 2 - (initial_box[3] - initial_box[1]) // 2 - initial_box[1],
        ),
        initial,
        font=font,
        fill=(55, 74, 59)
    )


def render_instagram(chat, participants, messages):
    chat_id, _, title, subtitle, theme = chat[:5]
    server_dir = Path(__file__).resolve().parents[1]
    font_path = server_dir / "static" / "fonts" / "Roboto-Regular.ttf"
    output_dir = server_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    is_dark = (theme or "light").lower() == "dark"
    background = (18, 18, 18) if is_dark else (255, 255, 255)
    foreground = (245, 245, 245) if is_dark else (31, 31, 31)
    secondary = (170, 170, 170) if is_dark else (118, 118, 118)
    divider = (53, 53, 53) if is_dark else (235, 235, 235)
    incoming = (40, 40, 40) if is_dark else (242, 242, 242)
    outgoing = (91, 126, 99)

    img = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(img)
    title_font = _font(font_path, 42)
    name_font = _font(font_path, 31)
    message_font = _font(font_path, 37)
    time_font = _font(font_path, 24)

    header_bottom = 168
    draw.line((0, header_bottom, WIDTH, header_bottom), fill=divider, width=2)
    other_participant = next(
        (participant for participant in participants if participant[3] != "me"),
        None
    )
    _draw_participant_avatar(
        img, draw, other_participant, server_dir,
        (PADDING, 42, PADDING + 82, 124)
    )
    draw.text((PADDING + 108, 48), title or "Instagram chat", font=title_font, fill=foreground)
    draw.text((PADDING + 108, 104), subtitle or "Instagram DM", font=time_font, fill=secondary)
    draw.text((WIDTH - PADDING - 48, 62), "···", font=title_font, fill=foreground)

    y = header_bottom + 58
    max_text_width = WIDTH - 2 * PADDING - 88
    line_height = 54
    bubble_gap = 22

    for message in messages:
        if len(message) < 9:
            continue
        _, _, sender_id, message_type, content, timestamp, direction, _, _ = message
        if message_type != "text" or not content:
            continue

        lines = _wrap_text(draw, content, message_font, max_text_width - 54)
        text_height = max(line_height, len(lines) * line_height)
        name = _participant_name(
            participants,
            sender_id,
            "You" if direction == "outbound" else title or "Friend"
        )
        incoming_message = direction != "outbound"
        bubble_width = min(
            max(draw.textbbox((0, 0), line, font=message_font)[2] for line in lines) + 56,
            max_text_width
        )
        bubble_height = text_height + (62 if incoming_message else 36)
        x = PADDING if incoming_message else WIDTH - PADDING - bubble_width

        if incoming_message:
            draw.text((x, y), name, font=time_font, fill=secondary)
            y += 36

        fill = incoming if incoming_message else outgoing
        draw.rounded_rectangle(
            (x, y, x + bubble_width, y + bubble_height),
            radius=30,
            fill=fill
        )
        text_y = y + 22
        for line in lines:
            draw.text((x + 28, text_y), line, font=message_font, fill=foreground)
            text_y += line_height

        if timestamp:
            time_width = draw.textbbox((0, 0), timestamp, font=time_font)[2]
            draw.text(
                (x + bubble_width - time_width - 18, y + bubble_height - 34),
                timestamp,
                font=time_font,
                fill=(232, 232, 232) if not incoming_message else secondary
            )

        y += bubble_height + bubble_gap

    footer_y = HEIGHT - 118
    draw.line((0, footer_y, WIDTH, footer_y), fill=divider, width=2)
    draw.text(
        (PADDING, footer_y + 34),
        "Message",
        font=time_font,
        fill=secondary
    )
    draw.rounded_rectangle(
        (WIDTH - PADDING - 120, footer_y + 24, WIDTH - PADDING, footer_y + 78),
        radius=24,
        outline=divider,
        width=2
    )

    output_path = (output_dir / f"instagram_{chat_id}.png").resolve()
    img.save(output_path)
    return str(output_path)
