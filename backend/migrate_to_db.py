"""
Migration script to move data from in-memory storage to database.
"""
from storage import context_store as memory_store
from db_storage import db_context_store
from relevance import relevance_engine
from logger import logger


def migrate_to_database():
    """Migrate all contexts from in-memory storage to database."""
    logger.info("Starting migration from in-memory to database storage...")
    
    # Get all contexts from memory
    contexts = memory_store.list_all(include_superseded=True)
    
    if not contexts:
        logger.info("No contexts to migrate")
        return
    
    logger.info(f"Found {len(contexts)} contexts to migrate")
    
    # Migrate each context
    for context in contexts:
        try:
            # Get embedding if it exists
            embedding = memory_store.get_embedding(context.id)
            
            # Add to database
            db_context_store.add(context, embedding)
            logger.debug(f"Migrated context {context.id}")
            
        except Exception as e:
            logger.error(f"Error migrating context {context.id}: {e}")
    
    # Verify migration
    db_contexts = db_context_store.list_all(include_superseded=True)
    logger.info(f"Migration complete! {len(db_contexts)} contexts now in database")


if __name__ == "__main__":
    migrate_to_database()
