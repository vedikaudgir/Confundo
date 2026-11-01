from pydantic import BaseModel


class ExampleResponse(BaseModel):
    slug: str
    title: str
    platform: str
    scenario: str
    tone: str
    fictional: bool
    image_url: str
