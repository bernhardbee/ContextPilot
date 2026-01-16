#!/usr/bin/env python3
"""
Migration script to add 'model' column to messages table.

This script adds the 'model' column to existing messages tables
to track which AI model generated each message.

Usage:
    python migration_add_message_model.py [--dry-run]

Options:
    --dry-run    Show what would be done without making changes
"""

import argparse
import sys
from sqlalchemy import text, inspect
from database import engine, get_db_session
from logger import logger


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_model_column(dry_run: bool = False) -> bool:
    """
    Add 'model' column to messages table.
    
    Args:
        dry_run: If True, only show what would be done
        
    Returns:
        True if successful or already exists, False if failed
    """
    try:
        # Check if column already exists
        if check_column_exists('messages', 'model'):
            logger.info("Column 'model' already exists in messages table")
            return True
        
        # SQL to add the column
        sql_command = "ALTER TABLE messages ADD COLUMN model VARCHAR NULL"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would execute: {sql_command}")
            return True
        
        # Execute the migration
        with get_db_session() as db:
            logger.info("Adding 'model' column to messages table...")
            db.execute(text(sql_command))
            logger.info("Successfully added 'model' column to messages table")
            
            # Verify the column was added
            if check_column_exists('messages', 'model'):
                logger.info("Migration completed successfully")
                return True
            else:
                logger.error("Migration failed: Column was not created")
                return False
                
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Add 'model' column to messages table",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting migration: Add 'model' column to messages table")
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")
    
    success = add_model_column(dry_run=args.dry_run)
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()