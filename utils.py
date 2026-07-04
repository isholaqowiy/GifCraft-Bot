import os
import shutil

TEMP_DIR = "temp_gif"

def ensure_temp_directory():
    """Guarantees the isolated temp directory exists before file generation runs."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def clear_user_cache(user_id: int):
    """Safely purges cached binary image instances mapped to a specific user ID."""
    if not os.path.exists(TEMP_DIR):
        return
    for filename in os.listdir(TEMP_DIR):
        if filename.startswith(f"user_{user_id}_"):
            try:
                os.remove(os.path.join(TEMP_DIR, filename))
            except Exception:
                pass

