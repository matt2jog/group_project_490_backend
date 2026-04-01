from fastapi import APIRouter, HTTPException, Depends
from src.api.roles.domain import CreateClientResponse
from src.api.dependencies import get_account_from_bearer

#models
from src.api.roles.domain import ClientDetails


from src.database.session import get_session
from src.database.account.models import Account
from src.database.client.models import Client, FitnessGoals

router = APIRouter(prefix="/roles/client", tags=["client"])

@router.post("/create_client_initial_survey", response_model=CreateClientResponse)
def create_coach_request(client_details: ClientDetails, db = Depends(get_session), acc: Account = Depends(get_account_from_bearer)):
    """
    Creates a client, modifies user account to show client_id=xxx
    Attaches pmt info and fitness goal from initial survey
    Errors when a user has a client_id
    """

    #client err thrown in DI scope
    if acc.coach_id is not None:
        raise HTTPException(409, detail="Cannot create a request for a coach role when one is open, or the role is given")
    #TODO add availability
    db.add(client_details.payment_information)

    db.flush()

    client = Client(payment_information_id=client_details.payment_information.id) # type: ignore
    db.add(client)

    db.flush()

    client_details.fitness_goals.client_id = client.id # type: ignore

    db.add(client_details.fitness_goals)

    db.commit()

    return CreateClientResponse(client_id=client.id) # type: ignore
