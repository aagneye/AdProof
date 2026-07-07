"""Provider async webhook callbacks."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/provider")
async def provider_callback():
  return {"received": True}
