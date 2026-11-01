from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from server.schemas.example_schema import ExampleResponse
from server.services.examples_service import get_example_image, list_examples


router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("", response_model=list[ExampleResponse])
def examples():
    return list_examples()


@router.get("/{slug}.png")
def example_image(slug: str):
    path = get_example_image(slug)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="Example not found")
    return FileResponse(
        path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
