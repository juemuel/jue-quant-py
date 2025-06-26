from fastapi import APIRouter
from data_source.concept_data import get_concept_board_top10
from app.schemas.response import ApiResponse

router = ConceptRouter = APIRouter(prefix="/concepts", tags=["Concepts"])

@router.get("/boards", response_model=ApiResponse)
async def get_board_ranking():
    df = get_concept_board_top10()
    return ApiResponse(status="success", data=df.to_dict(orient="records"))
