class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/SharedHabit"
    JWT_SECRET_KEY = "super-secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False