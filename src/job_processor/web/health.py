from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Say the process is up. Touches nothing else."""
    return {"status": "ok"}
