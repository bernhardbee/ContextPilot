"""
Tests for database migration script.
"""
import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from sqlalchemy import create_engine, text, inspect

# Import the migration script
import migration_add_message_model as migration
from database import Base


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary database file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"
    
    # Create engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    
    yield engine, db_url
    
    # Cleanup
    os.unlink(temp_file.name)


class TestMigration:
    """Tests for the migration script."""
    
    def test_check_column_exists_true(self, temp_db):
        """Test checking for existing column."""
        engine, _ = temp_db
        
        # Mock the migration module's engine
        with patch.object(migration, 'engine', engine):
            # Create messages table with model column
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT,
                        role TEXT,
                        content TEXT,
                        model TEXT
                    )
                """))
                conn.commit()
            
            # Test that column exists
            assert migration.check_column_exists('messages', 'model') is True
    
    def test_check_column_exists_false(self, temp_db):
        """Test checking for non-existing column."""
        engine, _ = temp_db
        
        # Mock the migration module's engine
        with patch.object(migration, 'engine', engine):
            # Create messages table without model column
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT,
                        role TEXT,
                        content TEXT
                    )
                """))
                conn.commit()
            
            # Test that column doesn't exist
            assert migration.check_column_exists('messages', 'model') is False
    
    def test_add_model_column_success(self, temp_db):
        """Test successfully adding model column."""
        engine, _ = temp_db
        
        # Create messages table without model column
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at DATETIME
                )
            """))
            conn.commit()
        
        # Mock the migration module's engine and session
        with patch.object(migration, 'engine', engine):
            with patch('migration_add_message_model.get_db_session') as mock_session:
                # Create mock session context manager
                mock_db = Mock()
                mock_session.return_value.__enter__.return_value = mock_db
                mock_session.return_value.__exit__.return_value = None
                
                # Mock the execute method to actually execute the SQL
                def mock_execute(sql_text):
                    with engine.connect() as conn:
                        conn.execute(sql_text)
                        conn.commit()
                
                mock_db.execute.side_effect = mock_execute
                
                # Run migration
                result = migration.add_model_column(dry_run=False)
                
                # Verify success
                assert result is True
                
                # Verify column was added
                assert migration.check_column_exists('messages', 'model') is True
    
    def test_add_model_column_dry_run(self, temp_db):
        """Test dry run mode."""
        engine, _ = temp_db
        
        # Create messages table without model column
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT
                )
            """))
            conn.commit()
        
        # Mock the migration module's engine
        with patch.object(migration, 'engine', engine):
            # Run dry run
            result = migration.add_model_column(dry_run=True)
            
            # Verify success but no changes
            assert result is True
            assert migration.check_column_exists('messages', 'model') is False
    
    def test_add_model_column_already_exists(self, temp_db):
        """Test when column already exists."""
        engine, _ = temp_db
        
        # Create messages table with model column
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    model TEXT
                )
            """))
            conn.commit()
        
        # Mock the migration module's engine
        with patch.object(migration, 'engine', engine):
            # Run migration
            result = migration.add_model_column(dry_run=False)
            
            # Should return True since column already exists
            assert result is True
    
    @patch('migration_add_message_model.logger')
    def test_add_model_column_failure(self, mock_logger, temp_db):
        """Test handling migration failure."""
        engine, _ = temp_db
        
        # Mock the migration module's engine
        with patch.object(migration, 'engine', engine):
            with patch('migration_add_message_model.get_db_session') as mock_session:
                # Simulate database error
                mock_session.side_effect = Exception("Database error")
                
                # Run migration
                result = migration.add_model_column(dry_run=False)
                
                # Verify failure
                assert result is False
                mock_logger.error.assert_called()
    
    @patch('sys.argv', ['migration_add_message_model.py'])
    @patch('migration_add_message_model.add_model_column')
    @patch('migration_add_message_model.logger')
    def test_main_success(self, mock_logger, mock_add_column):
        """Test main function success."""
        mock_add_column.return_value = True
        
        with pytest.raises(SystemExit) as exc_info:
            migration.main()
        
        assert exc_info.value.code == 0
        mock_add_column.assert_called_once_with(dry_run=False)
        mock_logger.info.assert_called()
    
    @patch('sys.argv', ['migration_add_message_model.py', '--dry-run'])
    @patch('migration_add_message_model.add_model_column')
    @patch('migration_add_message_model.logger')
    def test_main_dry_run(self, mock_logger, mock_add_column):
        """Test main function with dry-run flag."""
        mock_add_column.return_value = True
        
        with pytest.raises(SystemExit) as exc_info:
            migration.main()
        
        assert exc_info.value.code == 0
        mock_add_column.assert_called_once_with(dry_run=True)
        mock_logger.info.assert_called()
    
    @patch('sys.argv', ['migration_add_message_model.py'])
    @patch('migration_add_message_model.add_model_column')
    @patch('migration_add_message_model.logger')
    def test_main_failure(self, mock_logger, mock_add_column):
        """Test main function failure."""
        mock_add_column.return_value = False
        
        with pytest.raises(SystemExit) as exc_info:
            migration.main()
        
        assert exc_info.value.code == 1
        mock_add_column.assert_called_once_with(dry_run=False)
        mock_logger.error.assert_called()