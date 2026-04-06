from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from src.api.dependencies import get_account_from_bearer, get_client_account

#models
from src.api.roles.client.domain import InitialSurveyInput, ClientAccountResponse, CreateClientResponse, DunderResponse, UpdateClientInfoInput
 
from src.database.session import get_session
from src.database.account.models import Account
from src.database.client.models import Client, ClientAvailability, FitnessGoals
from src.database.payment.models import PaymentInformation
from src.database.telemetry.models import ClientTelemetry, HealthMetrics

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

@router.post("/update_client_information", response_model=DunderResponse)
def update_client_information(payload: UpdateClientInfoInput, db = Depends(get_session), acc: Account = Depends(get_client_account)):
    """
    Availabilities: providing availabilities will ADD availability, should REMOVE exisiting availability BEFORE calling this method if batch updating
    Fitness goals will override current reading
    Health metrics appends new record as client_telemetry
    Payment information is overridden

    Will merge timelines for multiple availabilities mapping to the client if new addition intersects
    """
    client = db.get(Client, acc.client_id)
    if client is None:
        raise HTTPException(404, detail="Client profile not found")

    if payload.availabilities:
        if client.client_availability_id is None:
            client_availability = ClientAvailability()
            db.add(client_availability)
            db.flush()
            client.client_availability_id = client_availability.id
        
        # not sure how to merge overlapping time ranges
        for availability in payload.availabilities:
            availability.client_availability_id = client.client_availability_id
            db.add(availability)

    if payload.fitness_goals:
        existing_goals = db.exec(select(FitnessGoals).where(FitnessGoals.client_id == client.id)).first()
        if existing_goals is not None:
            existing_goals.goal_enum = payload.fitness_goals.goal_enum
            db.add(existing_goals)
        else:
            payload.fitness_goals.client_id = client.id
            db.add(payload.fitness_goals)
    
    if payload.payment_information:
        if client.payment_information_id is not None:
            current_payment = db.get(PaymentInformation, client.payment_information_id)
            if current_payment is not None:
                current_payment.card_number = payload.payment_information.card_number
                current_payment.cvv = payload.payment_information.cvv
                current_payment.expiration_date = payload.payment_information.expiration_date
                db.add(current_payment)
            else:
                db.add(payload.payment_information)
                db.flush()
                client.payment_information_id = payload.payment_information.id
        else:
            db.add(payload.payment_information)
            db.flush()
            client.payment_information_id = payload.payment_information.id
    
    if payload.health_metrics:
        telem = ClientTelemetry(client_id=client.id, date=date.today())
        db.add(telem)
        db.flush()
        payload.health_metrics.client_telemetry_id = telem.id
        db.add(payload.health_metrics)
    db.add(client)
    db.commit()
    
    return DunderResponse()

@router.post("/me", response_model=ClientAccountResponse)
def me(db = Depends(get_session), acc: Account = Depends(get_client_account)):
    return ClientAccountResponse(
        base_account=acc,
        client_account=db.get(Client, acc.client_id)
    )

@router.delete("/delete_client_profile", response_model=DunderResponse)
def delete_client_profile(db = Depends(get_session), acc: Account = Depends(get_client_account)):
    client = db.get(Client, acc.client_id)
    if client is None:
        raise HTTPException(404, detail="Client profile not found")

    fitness_goals = db.exec(
        select(FitnessGoals).where(FitnessGoals.client_id == client.id)
    ).all()

    telemetry_rows = db.exec(
        select(ClientTelemetry).where(ClientTelemetry.client_id == client.id)
    ).all()

    health_metrics_rows = db.exec(
        select(HealthMetrics).where(
            HealthMetrics.client_telemetry_id.in_(
                [t.id for t in telemetry_rows if t.id is not None]
            )
        )
    ).all()

    acc.client_id = None
    db.add(acc)

    for goal in fitness_goals:
        db.delete(goal)

    db.flush()

    for metric in health_metrics_rows:
        db.delete(metric)

    db.flush()

    for telem in telemetry_rows:
        db.delete(telem)

    db.flush()

    db.delete(client)
    db.commit()

    return DunderResponse()