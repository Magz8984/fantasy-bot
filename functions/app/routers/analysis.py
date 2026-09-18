from fastapi import APIRouter

from app.squad_service import processSquadAnalysis

router = APIRouter(tags=["analysis"])


@router.post("/analyze")
def analyzeSquad():
    return processSquadAnalysis()
