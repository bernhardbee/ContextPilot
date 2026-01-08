#!/usr/bin/env python3
"""
Database migration management script.

Usage:
    python migrate.py upgrade head        # Apply all migrations
    python migrate.py downgrade -1        # Rollback one migration
    python migrate.py current             # Show current revision
    python migrate.py history             # Show migration history
    python migrate.py revision "message"  # Create new migration
"""
import sys
from alembic.config import Config
from alembic import command


def main():
    """Run alembic commands."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    
    cmd = sys.argv[1]
    
    if cmd == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        command.upgrade(alembic_cfg, revision)
        print(f"✅ Database upgraded to: {revision}")
    
    elif cmd == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        command.downgrade(alembic_cfg, revision)
        print(f"✅ Database downgraded to: {revision}")
    
    elif cmd == "current":
        command.current(alembic_cfg)
    
    elif cmd == "history":
        command.history(alembic_cfg)
    
    elif cmd == "revision":
        message = sys.argv[2] if len(sys.argv) > 2 else "auto migration"
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print(f"✅ Created new migration: {message}")
    
    elif cmd == "stamp":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        command.stamp(alembic_cfg, revision)
        print(f"✅ Stamped database at: {revision}")
    
    else:
        print(f"❌ Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
