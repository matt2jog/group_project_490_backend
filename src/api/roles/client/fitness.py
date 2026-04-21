from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, SQLModel

from src.database.session import get_session
from src.database.account.models import Account
from src.api.dependencies import get_client_account, PaginationParams
from src.database.client.models import (
    ClientWorkoutPlan, 
    DailyMoodSurvey, 
    CompletedSurvey,
)

router = APIRouter(prefix="/roles/client/fitness", tags=["client", "fitness"])

class DailySurveySubmitPayload(SQLModel):
    happiness_meter: int
    alertness: int
    healthiness: int
    todays_goals: str
    todays_appreciation: str

    @field_validator("happiness_meter", "alertness", "healthiness")
    @classmethod
    def validate_meter(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("Value must be between 1 and 10")
        return v

class DailySurveyResponse(SQLModel):
    survey_id: int
    telemetry_id: int
    is_seen: bool
    is_started: bool
    is_finished: bool
    completed_survey_id: Optional[int] = None

def get_or_create_daily_survey(db: Session, client_id: int) -> DailyMoodSurvey:
    today = date.today()

    telemetry = db.exec(
        select(ClientTelemetry).where(
            ClientTelemetry.client_id == client_id,
            ClientTelemetry.date == today
        )
    ).first()

    if telemetry is None:
        telemetry = ClientTelemetry(
            client_id=client_id,
            date=today
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

    survey = db.exec(
        select(DailyMoodSurvey).where(
            DailyMoodSurvey.client_telemetry_id == telemetry.id
        )
    ).first()
    
    if not survey:
        survey = DailyMoodSurvey(is_seen=True, is_started=False, is_finished=False, client_telemetry_id=telemetry.id)
        db.add(survey)
        db.commit()
        db.refresh(survey)
    return telemetry, survey

@router.get("/query/plans")
def query_client_workout_plans(
    pagination: PaginationParams = Depends(PaginationParams),
    db: Session = Depends(get_session),
    acc: Account = Depends(get_client_account)
):
    query = select(ClientWorkoutPlan).where(ClientWorkoutPlan.client_id == acc.client_id)
    plans = db.exec(query.offset(pagination.skip).limit(pagination.limit)).all()
    return plans

@router.get("/daily-survey/today", response_model=DailySurveyResponse)
def get_today_daily_survey(
    db: Session = Depends(get_session),
    acc: Account = Depends(get_client_account)
):
    
    if acc.client_id is None:
        raise HTTPException(status_code=404, detail="Client profile not found")
    
    telemetry, survey = get_or_create_daily_survey(db, acc.client_id)
    return DailySurveyResponse(
        survey_id=survey.id,
        telemetry_id=telemetry.id,
        is_seen=survey.is_seen,
        is_started=survey.is_started,
        is_finished=survey.is_finished,
        completed_survey_id=survey.completed_survey_id
    )

@router.post("/daily-survey/start", response_model=DailySurveyResponse)
def start_daily_survey(
    db: Session = Depends(get_session),
    acc: Account = Depends(get_client_account)
):
    if acc.client_id is None:
        raise HTTPException(status_code=404, detail="Client profile not found")
    
    telemetry, survey = get_or_create_daily_survey(db, acc.client_id)

    if survey.is_started:
        raise HTTPException(status_code=400, detail="Survey already started")

    survey.is_started = True
    db.add(survey)
    db.commit()
    db.refresh(survey)

    return DailySurveyResponse(
        survey_id=survey.id,
        telemetry_id=telemetry.id,
        is_seen=survey.is_seen,
        is_started=survey.is_started,
        is_finished=survey.is_finished,
        completed_survey_id=survey.completed_survey_id
    )

@router.post("/daily-survey/submit", response_model=DailySurveyResponse)
def submit_daily_survey(
    payload: DailySurveySubmitPayload,
    db: Session = Depends(get_session),
    acc: Account = Depends(get_client_account)
):
    if acc.client_id is None:
        raise HTTPException(status_code=404, detail="Client profile not found")
    
    telemetry, survey = get_or_create_daily_survey(db, acc.client_id)

    if not survey.is_started:
        raise HTTPException(status_code=400, detail="Survey has not been started yet")
    if survey.is_finished:
        raise HTTPException(status_code=400, detail="Survey has already been submitted")

    completed_survey = CompletedSurvey(
        client_telemetry_id=telemetry.id,
        happiness_meter=payload.happiness_meter,
        alertness=payload.alertness,
        healthiness=payload.healthiness,
        todays_goals=payload.todays_goals,
        todays_appreciation=payload.todays_appreciation
    )
    db.add(completed_survey)
    db.commit()
    db.refresh(completed_survey)

    survey.is_finished = True
    survey.completed_survey_id = completed_survey.id
    db.add