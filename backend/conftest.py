"""
Test configuration - force in-memory storage for tests
"""
import os

# Force in-memory storage for tests
os.environ["CONTEXTPILOT_USE_DATABASE"] = "false"
