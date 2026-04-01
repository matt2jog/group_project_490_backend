from src.database.base import SQLModelLU

from src.database.account import models as _account_models
from src.database.admin import models as _admin_models
from src.database.client import models as _client_models
from src.database.coach import models as _coach_models
from src.database.coach_client_relationship import models as _coach_client_relationship_models  # noqa: F401
from src.database.payment import models as _payment_models
from src.database.reports import models as _reports_models
from src.database.role_management import models as _role_management_models