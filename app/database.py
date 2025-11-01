from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Update the connection string for MySQL
# Replace 'username', 'password', 'host', 'port', and 'database_name' with your actual values
SQLALCHEMY_DATABASE_URL ="mysql+pymysql://root:root@54.221.81.208:3306/language_api" 
#"mysql+pymysql://language_user:StrongPassword@123@127.0.0.1:3306/language_api"
 #"mysql+pymysql://root:root@127.0.0.1:3306/languageapp_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

