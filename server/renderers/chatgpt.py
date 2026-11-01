from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
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

    draw.ellipse(box, fill=(68, 77, 70))
    initial = ((participant[2] if participant else None) or "C").strip()[:1].upper()
    font = _font(server_dir / "static" / "fonts" / "Roboto-Regular.ttf", 20)
    initial_box = draw.textbbox((0, 0), initial, font=font)
    draw.text(
        (
            x1 + size // 2 - (initial_box[2] - initial_box[0]) // 2,
            y1 + size // 2 - (initial_box[3] - initial_box[1]) // 2 - initial_box[1],
        ),
        initial,
        font=font,
        fill=(245, 245, 245)
    )


def render_chatgpt(chat, participants, messages):
    chat_id = chat[0]
    title = chat[2] or "ChatGPT"
    subtitle = chat[3] or "A conversation"
    is_dark = len(chat) < 5 or (chat[4] or "dark").lower() != "light"

    server_dir = Path(__file__).resolve().parents[1]
    font_path = server_dir / "static" / "fonts" / "Roboto-Regular.ttf"
    output_dir = server_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    background = (32, 33, 35) if is_dark else (255, 255, 255)
    header = (40, 41, 43) if is_dark else (247, 247, 248)
    assistant_bubble = (52, 53, 55) if is_dark else (244, 244, 245)
    user_bubble = (64, 65, 68) if is_dark else (235, 239, 234)
    foreground = (245, 245, 245) if is_dark else (37, 39, 38)
    muted = (174, 177, 181) if is_dark else (112, 116, 113)

    title_font = _font(font_path, 42)
    name_font = _font(font_path, 27)
    message_font = _font(font_path, 37)
    time_font = _font(font_path, 23)

    messages_to_draw = [
        message for message in messages
        if len(message) >= 9 and message[3] == "text" and message[4]
    ]
    prepared = []
    y = 190
    line_height = 54
    max_text_width = WIDTH - 2 * PADDING - 48
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    for message in messages_to_draw:
        _, _, sender_id, _, content, timestamp, direction, _, _ = message
        lines = _wrap_text(draw, content, message_font, max_text_width)
        name = _participant_name(
            participants,
            sender_id,
            "You" if direction == "outbound" else title
        )
        text_height = max(line_height, line_height * len(lines))
        bubble_height = text_height + (87 if timestamp else 65)
        prepared.append((message, lines, name, bubble_height))
        y += 38 + bubble_height + 28

    height = max(1200, y + 145)
    img = Image.new("RGB", (WIDTH, height), background)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 150), fill=header)
    draw.text((PADDING, 36), title, font=title_font, fill=foreground)
    draw.text((PADDING, 96), subtitle, font=time_font, fill=muted)

    y = 190
    for message, lines, name, bubble_height in prepared:
        _, _, sender_id, _, _, timestamp, direction, _, _ = message
        outbound = direction == "outbound"
        bubble_width = WIDTH - 2 * PADDING
        x = PADDING
        participant = next(
            (item for item in participants if item[0] == sender_id),
            None
        )
        _draw_participant_avatar(
            img, draw, participant, server_dir, (x, y, x + 34, y + 34)
        )
        draw.text((x + 49, y + 3), name, font=name_font, fill=muted)
        y += 38

        bubble_color = user_bubble if outbound else assistant_bubble
        draw.rounded_rectangle(
            (x, y, x + bubble_width, y + bubble_height),
            radius=20,
            fill=bubble_color
        )

        text_y = y + 24
        for line in lines:
            draw.text(
                (x + 26, text_y),
                line,
                font=message_font,
                fill=foreground
            )
            text_y += line_height

        if timestamp:
            time_width = draw.textbbox((0, 0), timestamp, font=time_font)[2]
            draw.text(
                (x + bubble_width - time_width - 22, y + bubble_height - 37),
                timestamp,
                font=time_font,
                fill=muted
            )

        y += bubble_height + 28

    draw.line(
        (PADDING, height - 90, WIDTH - PADDING, height - 90),
        fill=(66, 67, 69) if is_dark else (226, 228, 226),
        width=2
    )
    draw.text(
        (PADDING, height - 62),
        "Message",
        font=time_font,
        fill=muted
    )

    output_path = (output_dir / f"chatgpt_{chat_id}.png").resolve()
    img.save(output_path)
    return str(output_path)
