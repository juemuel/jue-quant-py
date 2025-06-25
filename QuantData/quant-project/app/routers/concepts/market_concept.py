from fastapi import APIRouter
from ....data_source.concept_data import qs, realtime_data

router = ConceptRouter = APIRouter(prefix="/concepts", tags=["Concepts"])

@router.get("/boards")
async def get_board_ranking():
    df = qs.realtime_data("概念板块").head(10)
    return {"data": df.to_dict(orient="records")}