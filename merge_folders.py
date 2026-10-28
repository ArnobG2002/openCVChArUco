import os
import shutil

# Change these to your actual directory paths
source_dir = r"C:\openCV\Liberal"
dest_dir = r"C:\openCV\chaarAdhyay"

def safe_merge(source, dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
        
    # Iterate through every item inside the source folder
    for item in os.listdir(source):
        source_item = os.path.join(source, item)
        dest_item = os.path.join(dest, item)
        
        # If a name collision occurs
        if os.path.exists(dest_item):
            base, ext = os.path.splitext(item)
            counter = 1
            # Loop until a completely unique folder/file name is found
            while os.path.exists(dest_item):
                new_name = f"{base}_{counter}{ext}" if ext else f"{base}_{counter}"
                dest_item = os.path.join(dest, new_name)
                counter += 1
                
        # Move the item over completely intact (without merging subfolder contents)
        shutil.move(source_item, dest_item)

safe_merge(source_dir, dest_dir)
print("Folder consolidation complete with separated subfolders!")
