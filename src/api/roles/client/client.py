import os, requests
from datetime import date, datetime, time

from fastapi import APIRouter, HTTPException, Depends, UploadFile, Query
from typing import Optional, List
from sqlmodel import select
from sqlalchemy import func, desc, asc

from src import config
from src.api.dependencies import get_account_from_bearer, get_client_account, PaginationParams

#models
from src.api.roles.client.domain import (
    InitialSurveyInput,
    ClientAccountResponse,
    CreateClientResponse,
    DunderResponse,
    UpdateClientInfoInput,
    ClientCoachRequestResponse,
    HirableCoachItem,
)

from src.database.session import get_session
from src.database.coach.models import Coach, Experience, Certifications, CoachExperience, CoachCertifications
from src.database.coach_client_relationship.models import ClientCoachRequest
from src.database.account.models import Account, Availability
from src.database.client.models import Client, ClientAvailability
from src.database.telemetry.models import ClientTelemetry
from src.database.reports.models import CoachReviews
from src.database.payment.models import PaymentInformation

router = APIRouter(prefix="/roles/client", tags=["client"])

@router.post("/initial_survey", response_model=CreateClientResponse)
def log_initial_survey(client_details: InitialSurveyInput, db = Depends(get_session), acc: Account = Depends(get_account_from_bearer)):
    """
    Creates a client, modifies user account to show client_id=xxx
    Attaches pmt info and fitness goal from initial survey
    Errors when a user has a client_id
    """

    if acc.client_id is not None:
        raise HTTPException(409, detail="Client profile already exists for this account")

    db.add(client_details.payment_information)
    for availability in client_details.availabilities:
        db.add(availability)
    
    db.flush()

    client_availability = ClientAvailability()
    db.add(client_availability)
    db.flush()

    for a in client_details.availabilities:
        a.client_availability_id = client_availability.id

    client = Client(
        payment_information_id=client_details.payment_information.id,
        client_availability_id=client_availability.id,
    )

    db.add(client)
    db.flush()

    telem = ClientTelemetry(client_id=client.id, date=date.today())
    db.add(telem)
    
    client_details.fitness_goals.client_id = client.id  # type: ignore
    db.add(client_details.fitness_goals)

    acc.client_id = client.id
    
    db.flush()

    client_details.initial_health_metric.client_telemetry_id = telem.id

    db.add(client_details.initial_health_metric)
    
    db.commit()

    return CreateClientResponse(client_id=client.id) # type: ignore



@router.patch("/information", response_model=DunderResponse)
def update_client_information(payload: UpdateClientInfoInput, db = Depends(get_session), acc: Account = Depends(get_client_account)):
    """
    Availabilities: providing availabilities will ADD availability, should REMOVE exisiting availability BEFORE calling this method if batch updating
    Fitness goals will override current reading
    Health metrics appends new record as client_telemetry
    Payment information is overridden

    Will merge timelines for multiple availabilities mapping to the client if new addition intersects
    """
    if payload.availabilities: 
        pass
    if payload.fitness_goals:
        pass
    if payload.health_metrics:
        pass
    if payload.payment_information:
        pass

    return DunderResponse()

@router.post("/me", response_model=ClientAccountResponse)
def me(db = Depends(get_session), acc: Account = Depends(get_client_account)):
    return ClientAccountResponse(
        base_account=acc,
        client_account=db.get(Client, acc.client_id)
    )



@router.post("/request_coach/{coach_id}", response_model=ClientCoachRequestResponse)
def create_coach_request(coach_id: int, db = Depends(get_session), acc: Account = Depends(get_client_account)):
    """
    Creates a coach request from a client to a coach. Errors if a pending request already exists
    """
    client = db.get(Client, acc.client_id)
    coach = db.get(Coach, coach_id)

    if coach is None:
        raise HTTPException(404, detail="Coach not found")
    
    existing_request = db.query(ClientCoachRequest).filter_by(
        client_id=client.id, coach_id=coach.id, is_accepted=None
    ).first()

    if existing_request:
        raise HTTPException(409, detail="A pending request to this coach already exists")

    request = ClientCoachRequest(client_id=client.id, coach_id=coach.id, is_accepted=None)
    db.add(request)

    # actually commit
    db.commit()
    db.refresh(request)

    return ClientCoachRequestResponse(request_id=request.id)

@router.post("/upload_progress_picture")
def upload_progress_picture(file: UploadFile, acc: Account = Depends(get_client_account)):
    """Upload an image to the `progress_picture` bucket and return the public URL.

    This endpoint intentionally does not modify the database yet.
    """

    SUPABASE_URL = config.SUPABASE_URL or os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = config.SUPABASE_SERVICE_KEY or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(500, detail="Supabase storage is not configured on the server")

    bucket = "progress_picture"
    filename = f"{acc.id}_{file.filename}"
    upload_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}/{filename}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
    }

    try:
        resp = requests.put(upload_url, data=file.file, headers=headers)
    except Exception as e:
        raise HTTPException(500, detail=f"Upload failed: {e}")

    if resp.status_code not in (200, 201, 204):
        raise HTTPException(resp.status_code, detail=f"Upload failed: {resp.text}")

    public_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{bucket}/{filename}"
    return {"url": public_url}


@router.get("/query/hirable_coaches", response_model=List[HirableCoachItem])
def query_hirable_coaches(
    name: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    age_start: Optional[int] = Query(None),
    age_end: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("avg_rating"),
    order: Optional[str] = Query("desc"),
    pagination: PaginationParams = Depends(PaginationParams),
    db = Depends(get_session),
    acc: Account = Depends(get_client_account),
):
    """
    Query verified/active coaches by optional filters (name, specialty, age range, gender).
    Sort by `avg_rating` or `rating_count` with `order` asc/desc.
    Returns a list of coaches with `avg_rating` and `rating_count` included.
    """

    # base filters: coach must be verified and account active
    stmt = select(
        Coach.id.label("coach_id"), # type: ignore
        Account.name.label("name"),
        Account.email.label("email"),
        Account.age.label("age"),
        Account.gender.label("gender"),
        Coach.specialties.label("specialties"),
        func.count(CoachReviews.id).label("rating_count"),
        func.avg(CoachReviews.rating).label("avg_rating"),
    ).join(Account, Account.coach_id == Coach.id).outerjoin(CoachReviews, CoachReviews.coach_id == Coach.id)

    # filters
    where_clauses = [Account.is_active == True, Coach.verified == True]

    if name:
        where_clauses.append(func.lower(Account.name).like(f"%{name.lower()}%"))

    if specialty:
        # specialties stored as comma-separated string in DB; partial match
        where_clauses.append(func.lower(Coach.specialties).like(f"%{specialty.lower()}%"))

    if age_start is not None:
        where_clauses.append(Account.age >= age_start)
    if age_end is not None:
        where_clauses.append(Account.age <= age_end)
    if gender:
        where_clauses.append(func.lower(Account.gender) == gender.lower())

    stmt = stmt.where(*where_clauses)

    # group and ordering
    stmt = stmt.group_by(Coach.id, Account.id, Account.name, Account.email, Account.age, Account.gender, Coach.specialties)

    if sort_by == "rating_count":
        order_expr = desc(func.count(CoachReviews.id)) if order == "desc" else asc(func.count(CoachReviews.id))
        stmt = stmt.order_by(order_expr)
    else:
        # default sort by avg_rating
        order_expr = desc(func.avg(CoachReviews.rating)) if order == "desc" else asc(func.avg(CoachReviews.rating))
        stmt = stmt.order_by(order_expr)

    stmt = stmt.offset(pagination.skip).limit(pagination.limit)

    rows = db.exec(stmt).all()

    result = []
    for r in rows:
        # fetch experiences and certifications for this coach
        exps = db.exec(
            select(Experience).join(CoachExperience, CoachExperience.experience_id == Experience.id).where(CoachExperience.coach_id == r.coach_id)
        ).all()
        certs = db.exec(
            select(Certifications).join(CoachCertifications, CoachCertifications.certification_id == Certifications.id).where(CoachCertifications.coach_id == r.coach_id)
        ).all()

        result.append(
            {
                "coach_id": r.coach_id,
                "name": r.name,
                "email": r.email,
                "age": r.age,
                "gender": r.gender,
                "specialties": r.specialties,
                "avg_rating": float(r.avg_rating) if r.avg_rating is not None else None,
                "rating_count": int(r.rating_count) if r.rating_count is not None else 0,
                "experiences": exps,
                "certifications": certs,
            }
        )

    return result
