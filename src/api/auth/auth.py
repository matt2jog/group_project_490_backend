from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from src.api.auth.domain import AuthTokenResponse, LoginRequest, SignupRequest
from src.api.auth.services import create_account
from src.api.dependencies import authenticate_user, create_jwt_token
from src.database.account.models import Account
from src.database.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_token(user: Account) -> AuthTokenResponse:
    token = create_jwt_token(user)
    return AuthTokenResponse(access_token=token)


@router.post("/signup", response_model=AuthTokenResponse)
def signup(
    data: SignupRequest,
    db: Session = Depends(get_session),
):
    existing_user = db.exec(select(Account).where(Account.email == data.email)).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists",
        )

    user = create_account(data)
    db.add(user)
    db.commit()
    db.refresh(user)

    return issue_token(user)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_session),
):
    user = authenticate_user(db, data.email, data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return issue_token(user)


@router.post("/token", response_model=AuthTokenResponse)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return issue_token(user)