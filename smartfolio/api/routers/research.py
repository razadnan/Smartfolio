from fastapi import APIRouter, HTTPException, Query
from smartfolio.api.schemas import PromotionLog
from smartfolio.api.services import results_reader as rr
from smartfolio.api.services.promotions import summarize

router = APIRouter(tags=["research"])


@router.get("/champion-challenger", response_model=PromotionLog)
def champion_challenger():
    try:
        return summarize(rr.promotions())
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/feedback")
def feedback_overview():
    try:
        pred = rr.feedback("prediction")
        port = rr.feedback("portfolio")
        return {"prediction_total": len(pred), "portfolio_periods": len(port), "portfolio": port}
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/feedback/prediction")
def prediction_feedback(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    try:
        rows = rr.feedback("prediction")
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})
    return {"total": len(rows), "limit": limit, "offset": offset,
            "rows": rows[offset:offset + limit]}
