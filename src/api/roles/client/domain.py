from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from fastapi import HTTPException
#Client
from src.database.client.models import FitnessGoals
from src.database.payment.models import PaymentInformation
from src.database.account.models import Availability, Account
from src.database.telemetry.models import HealthMetrics
from src.database.client.models import Client
from src.database.reports.models import CoachReport, CoachReviews

class InitialSurveyInput(BaseModel): #creates a client
    fitness_goals: FitnessGoals
    payment_information: PaymentInformation
    availabilities: List[Availability]
    initial_health_metric: HealthMetrics

class UpdateClientInfoInput(BaseModel):
    fitness_goals: Optional[FitnessGoals] = Field(default=None) #reset fitness goals
    payment_information: Optional[PaymentInformation] = Field(default=None) #reset pmt info
    availabilities: Optional[List[Availability]] = Field(default=None) #new availabilities
    health_metrics: Optional[HealthMetrics] = Field(default=None)

    @model_validator(mode="after") #runs after model is validated from typing standards
    def ensure_not_empty(self):
        if not any((
            self.fitness_goals, 
            self.payment_information, 
            self.availabilities,
            self.health_metrics
        )):
            raise HTTPException(422, detail="Cannot update with no update parameters")
        
        return self #return the "safe" validated model, which is just itself (no need to cast / do anything else)



#Responses

class CoachReportResponse(BaseModel):
    report_id: int

class ReportsResponse(BaseModel):
    reports: List[CoachReport]

class CoachReviewResponse(BaseModel):
    review_id: int

class ReviewsResponse(BaseModel):
    reviews: List[CoachReviews]

class ClientCoachRequestResponse(BaseModel):
    request_id: int

class CreateClientResponse(BaseModel):
    client_id: int

class ClientAccountResponse(BaseModel):
    base_account: Account
    client_account: Client

class DunderResponse(BaseModel):
    details: str = "success"