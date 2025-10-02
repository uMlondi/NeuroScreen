import os
import shutil
import tempfile

def clear_pycache_dirs(root_dir='.'):
    pycache_dirs = []
    for root, dirs, files in os.walk(root_dir):
        for d in dirs:
            if d == '__pycache__':
                full_path = os.path.join(root, d)
                pycache_dirs.append(full_path)
    for d in pycache_dirs:
        shutil.rmtree(d)
    print(f"Deleted __pycache__ directories: {pycache_dirs}")

def clear_jinja_cache():
    temp_dir = tempfile.gettempdir()
    jinja_cache_dir = os.path.join(temp_dir, 'jinja2')
    if os.path.exists(jinja_cache_dir):
        shutil.rmtree(jinja_cache_dir)
        print(f"Deleted Jinja2 cache directory: {jinja_cache_dir}")
    else:
        print("No Jinja2 cache directory found")

if __name__ == "__main__":
    clear_pycache_dirs()
    clear_jinja_cache()
