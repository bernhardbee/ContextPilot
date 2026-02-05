"""
Test configuration - force in-memory storage for tests
"""
import os
import warnings

# Force in-memory storage for tests
os.environ["CONTEXTPILOT_USE_DATABASE"] = "false"

# Suppress urllib3 LibreSSL warning in test output
warnings.filterwarnings(
	"ignore",
	message=".*LibreSSL.*",
	category=Warning,
	module="urllib3",
)
