# organize.py
import os, shutil
from datetime import datetime

def organize_files(source_dir, method="extension"):
    """
    Sort files in source_dir by type or date.
    method: "extension" or "date"
    """
    for filename in os.listdir(source_dir):
        filepath = os.path.join(source_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if method == "extension":
            ext = os.path.splitext(filename)[1].lstrip(".").lower()
            if not ext:
                continue
            target_folder = os.path.join(source_dir, ext)
        else:  # method == "date"
            mtime = os.path.getmtime(filepath)
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m")
            target_folder = os.path.join(source_dir, date_str)
        # Create target folder if needed
        os.makedirs(target_folder, exist_ok=True)
        # Move file
        shutil.move(filepath, os.path.join(target_folder, filename))

# Example usage (from CLI or another script):
# organize_files("/Users/you/Downloads", method="extension")
