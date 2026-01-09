"""
Settings persistence layer for ContextPilot.
Stores API keys and configuration in database for persistence across restarts.
"""
from sqlalchemy import Column, String, Float, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from logger import logger

Base = declarative_base()


class SettingsModel(Base):
    """Database model for persisted settings."""
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class SettingsStore:
    """Manages persistent storage of application settings."""
    
    def __init__(self, database_url: str):
        """Initialize settings store with database connection."""
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("Settings store initialized")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a setting value by key.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        session = self.SessionLocal()
        try:
            setting = session.query(SettingsModel).filter(SettingsModel.key == key).first()
            return setting.value if setting else default
        finally:
            session.close()
    
    def set(self, key: str, value: str) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        session = self.SessionLocal()
        try:
            setting = session.query(SettingsModel).filter(SettingsModel.key == key).first()
            if setting:
                setting.value = value
            else:
                setting = SettingsModel(key=key, value=value)
                session.add(setting)
            session.commit()
            logger.info(f"Setting '{key}' updated")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to set setting '{key}': {e}")
            raise
        finally:
            session.close()
    
    def delete(self, key: str) -> None:
        """
        Delete a setting.
        
        Args:
            key: Setting key
        """
        session = self.SessionLocal()
        try:
            setting = session.query(SettingsModel).filter(SettingsModel.key == key).first()
            if setting:
                session.delete(setting)
                session.commit()
                logger.info(f"Setting '{key}' deleted")
        finally:
            session.close()
    
    def get_all(self) -> dict:
        """
        Get all settings as a dictionary.
        
        Returns:
            Dictionary of all settings
        """
        session = self.SessionLocal()
        try:
            settings = session.query(SettingsModel).all()
            return {s.key: s.value for s in settings}
        finally:
            session.close()


# Global settings store instance (initialized later)
settings_store: Optional[SettingsStore] = None


def init_settings_store(database_url: str) -> SettingsStore:
    """
    Initialize the global settings store.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Initialized settings store
    """
    global settings_store
    settings_store = SettingsStore(database_url)
    return settings_store
