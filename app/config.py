import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/SharedHabit"
    )
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False