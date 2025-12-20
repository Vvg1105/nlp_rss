from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

if os.path.exists('/run/secrets/db-password'):
    # Reading password from docker secret file
    with open('/run/secrets/db-password', 'r') as f:
        DB_PASSWORD = f.read().strip()
else:
    # Reading password when running locally
    DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    print(SQLALCHEMY_DATABASE_URL)
    
    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Import models INSIDE __main__ to avoid circular import at module level
        from backend.models.article_table import Article
        from backend.models.event_table import Event
        
        # Use the Base that the models actually registered with!
        ModelBase = Article.__bases__[0]
        
        print(f"\nUsing Base from models to create tables...")
        print(f"Registered tables: {list(ModelBase.metadata.tables.keys())}")
        
        # Create all tables using the CORRECT Base
        print("\nCreating tables...")
        ModelBase.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in result]
            if tables:
                print(f"✅ Tables created successfully in database: {tables}")
            else:
                print("⚠️ No tables found in database!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
