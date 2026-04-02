import os
from dataclasses import dataclass
from dotenv import load_dotenv
from sqlmodel import create_engine

load_dotenv(ENV_LOCATION := os.path.abspath(
    os.path.join(os.path.basename(__file__), "..", ".env")
))

print(f"Loaded dotenv @ {ENV_LOCATION}")

if (db_conn_str := os.getenv("DATABASE_URL", None)) is None:
    raise Exception("Error, no database connection string found")

if (jwt_secret := os.getenv("JWT_SECRET", None)) is None:
    raise Exception("Error, no JWT_SECRET found")

if (gcp_client_id := os.getenv("GCP_CLIENT_ID", None)) is None:
    raise Exception("Error, no gcp_client_id found")

if (pass_salt := os.getenv("PASSWORD_SALT", None)) is None:
    raise Exception("Error, no password salt found")

jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

...

#try to coerce into sqlalch and see if it actually connects
try:
    create_engine(db_conn_str).connect()
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")   

@dataclass
class config:
    DATABASE_URL: str = db_conn_str
    
    PASSWORD_SALT: str = pass_salt
    JWT_SECRET: str = jwt_secret
    ALGORITHM: str = jwt_algorithm

    GCP_CLIENT_ID: str = gcp_client_id

print("Config loaded successfully!\n\n")
