import os
import sys
import time
import subprocess

# You can change this to "gdelt_gui_test.py" or whatever file you are currently editing
FILE_TO_WATCH = "gdelt_gui.py"
SRC_DIR = "src"

def get_mtime():
    try:
        return os.stat(FILE_TO_WATCH).st_mtime
    except FileNotFoundError:
        return 0

def get_src_mtime():
    """Get the latest modification time from all files in the src directory"""
    if not os.path.exists(SRC_DIR):
        return 0
    
    latest_mtime = 0
    for root, dirs, files in os.walk(SRC_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                mtime = os.stat(filepath).st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
            except FileNotFoundError:
                pass
    
    return latest_mtime

def main():
    if not os.path.exists(FILE_TO_WATCH):
        print(f"Error: {FILE_TO_WATCH} not found.")
        return

    last_mtime = get_mtime()
    last_src_mtime = get_src_mtime()
    # Start the application
    process = subprocess.Popen([sys.executable, FILE_TO_WATCH])
    
    print(f"Watching {FILE_TO_WATCH} and {SRC_DIR}/ for changes... (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(0.5)  # Check every half second
            current_mtime = get_mtime()
            current_src_mtime = get_src_mtime()
            
            # If the file or src files were modified, restart the process
            if current_mtime != last_mtime or current_src_mtime != last_src_mtime:
                if current_mtime != last_mtime:
                    print(f"\n[!] Detected change in {FILE_TO_WATCH}. Restarting UI...")
                else:
                    print(f"\n[!] Detected change in {SRC_DIR}/. Restarting UI...")
                process.terminate()
                process.wait()  # Wait for it to close
                
                # Restart
                process = subprocess.Popen([sys.executable, FILE_TO_WATCH])
                last_mtime = current_mtime
                last_src_mtime = current_src_mtime
                
    except KeyboardInterrupt:
        print("\nStopping watcher.")
        process.terminate()

if __name__ == "__main__":
    main()
