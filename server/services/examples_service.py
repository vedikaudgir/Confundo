from pathlib import Path
from uuid import uuid4

from server.services.chat_service import _render_chat


EXAMPLES = [
    {
        "slug": "roommate-rent",
        "title": "The rent reminder",
        "platform": "whatsapp",
        "scenario": "Roommates",
        "tone": "Everyday absurdity",
        "subtitle": "roommates",
        "messages": [
            ("other", "Rent is due tomorrow, just a heads-up.", "9:04 AM"),
            ("me", "I know. I have been emotionally preparing.", "9:05 AM"),
            ("other", "For the bank transfer?", "9:05 AM"),
            ("me", "For the notification from the bank.", "9:06 AM"),
        ],
    },
    {
        "slug": "plant-parent",
        "title": "A very dramatic plant",
        "platform": "whatsapp",
        "scenario": "Plant parents",
        "tone": "Deadpan",
        "subtitle": "last seen today",
        "messages": [
            ("me", "I moved your plant away from the window.", "7:42 PM"),
            ("other", "Why would you do that?", "7:43 PM"),
            ("me", "It looked like it needed a change of scenery.", "7:43 PM"),
            ("other", "That's a basil plant.", "7:44 PM"),
            ("me", "And now it has a story.", "7:44 PM"),
        ],
    },
    {
        "slug": "calendar-date",
        "title": "The calendar date",
        "platform": "instagram",
        "scenario": "First dates",
        "tone": "Awkwardly sweet",
        "subtitle": "Active now",
        "messages": [
            ("other", "Still on for coffee at 4?", "3:12 PM"),
            ("me", "Absolutely. I will be the one holding a coffee.", "3:12 PM"),
            ("other", "Helpful. What kind?", "3:13 PM"),
            ("me", "The nervous kind.", "3:13 PM"),
        ],
    },
    {
        "slug": "group-project",
        "title": "The group project",
        "platform": "instagram",
        "scenario": "Classmates",
        "tone": "Dry humor",
        "subtitle": "Active 2h ago",
        "messages": [
            ("me", "I finished the slides.", "10:21 AM"),
            ("other", "Amazing. Did you add the sources?", "10:22 AM"),
            ("me", "I added a slide that says sources.", "10:22 AM"),
            ("other", "That is not what I meant.", "10:23 AM"),
        ],
    },
    {
        "slug": "meeting-summary",
        "title": "The meeting summary",
        "platform": "chatgpt",
        "scenario": "Office hours",
        "tone": "Polite panic",
        "subtitle": "New chat",
        "messages": [
            ("me", "Summarize this meeting in one sentence.", "11:08 AM"),
            ("other", "We agreed to schedule another meeting.", "11:08 AM"),
            ("me", "Can you make it sound more productive?", "11:09 AM"),
            ("other", "We established a clear next step: scheduling another meeting.", "11:09 AM"),
        ],
    },
    {
        "slug": "weekend-plans",
        "title": "Weekend plans",
        "platform": "chatgpt",
        "scenario": "Making plans",
        "tone": "Low-stakes drama",
        "subtitle": "New chat",
        "messages": [
            ("me", "Help me plan a relaxing Saturday.", "8:31 PM"),
            ("other", "Start with a slow morning and one small activity.", "8:31 PM"),
            ("me", "What if the small activity is making a list of activities?", "8:32 PM"),
            ("other", "Then the list is the activity. You may stop there.", "8:32 PM"),
        ],
    },
]


def list_examples():
    return [
        {
            "slug": example["slug"],
            "title": example["title"],
            "platform": example["platform"],
            "scenario": example["scenario"],
            "tone": example["tone"],
            "fictional": True,
            "image_url": f"/examples/{example['slug']}.png",
        }
        for example in EXAMPLES
    ]


def get_example_image(slug):
    example = next((item for item in EXAMPLES if item["slug"] == slug), None)
    if example is None:
        return None

    server_dir = Path(__file__).resolve().parents[1]
    output_dir = server_dir / "static" / "examples"
    output_path = output_dir / f"{slug}.png"
    if output_path.exists():
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)
    participants = [
        (1, slug, "You", "me", None),
        (2, slug, example["scenario"], "other", None),
    ]
    messages = []
    for index, (sender, content, timestamp) in enumerate(example["messages"], start=1):
        messages.append(
            (
                index,
                slug,
                1 if sender == "me" else 2,
                "text",
                content,
                timestamp,
                "outbound" if sender == "me" else "inbound",
                None,
                None,
            )
        )

    chat = (
        f"{slug}-{uuid4().hex}",
        example["platform"],
        example["title"],
        example["subtitle"],
        "light",
    )
    rendered_path = Path(_render_chat(chat, participants, messages))
    rendered_path.replace(output_path)
    return output_path
