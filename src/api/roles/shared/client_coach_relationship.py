from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends
from src.api.dependencies import get_account_from_bearer, get_client_account, get_coach_account

from src.database.session import get_session

from src.api.roles.coach.domain import DunderResponse
from src.database.account.models import Account
from src.database.client.models import Client
from src.database.coach.models import Coach
from src.database.coach_client_relationship.models import ClientCoachRequest, ClientCoachRelationship


from src.api.roles.shared.domain import DeleteRequestResponse
router = APIRouter(prefix="roles/shared/client_coach_relationship/", tags=["shared", "client_coach_relationship"])


@router.delete("/delete_coach_request/{request_id}", response_model=DeleteRequestResponse)
def delete_coach_request(request_id: int, db = Depends(get_session), acc: Account = Depends(get_client_account)):
    """
    Deletes a coach request. Can be used by client to delete pending request, or by coach to reject a pending request
    """
    request = db.get(ClientCoachRequest, request_id)

    if request is None:
        raise HTTPException(404, detail="Request not found")
    
    if request.client_id != acc.client_id:
        raise HTTPException(403, detail="Not authorized to delete this request")
    
    db.delete(request)
    db.commit()

    return DeleteRequestResponse()

@router.post("/terminate_relationship/{relationship_id}", response_model=DunderResponse)
def terminate_relationship(relationship_id: int, db = Depends(get_session), acc: Account = Depends(get_account_from_bearer)):
    """
    Deletes a client-coach relationship. Both client and coach can delete the relationshio
    """

    relationship = db.get(ClientCoachRelationship, relationship_id)

    if relationship in None:
        raise HTTPException(404, detail="Relationship not found")
    
    relationship.is_active = False

    db.commit()

    return DunderResponse()


    

