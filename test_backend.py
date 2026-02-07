import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from app import backend
    print("Backend imported successfully")
    print(f"Logger: {backend.logger}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
