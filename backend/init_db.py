"""
Initialize the database and create tables.
"""
from database import init_db, engine
from db_models import Base
from logger import logger


def main():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully!")
    logger.info(f"Tables created: {', '.join(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    main()
