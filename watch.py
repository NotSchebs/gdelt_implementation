import os
import sys
import time
import subprocess

# You can change this to "gdelt_gui_test.py" or whatever file you are currently editing
FILE_TO_WATCH = "gdelt_gui_test.py"

def get_mtime():
    try:
        return os.stat(FILE_TO_WATCH).st_mtime
    except FileNotFoundError:
        return 0

def main():
    if not os.path.exists(FILE_TO_WATCH):
        print(f"Error: {FILE_TO_WATCH} not found.")
        return

    last_mtime = get_mtime()
    # Start the application
    process = subprocess.Popen([sys.executable, FILE_TO_WATCH])
    
    print(f"Watching {FILE_TO_WATCH} for changes... (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(0.5)  # Check every half second
            current_mtime = get_mtime()
            
            # If the file was modified, restart the process
            if current_mtime != last_mtime:
                print(f"\n[!] Detected change in {FILE_TO_WATCH}. Restarting UI...")
                process.terminate()
                process.wait()  # Wait for it to close
                
                # Restart
                process = subprocess.Popen([sys.executable, FILE_TO_WATCH])
                last_mtime = current_mtime
                
    except KeyboardInterrupt:
        print("\nStopping watcher.")
        process.terminate()

if __name__ == "__main__":
    main()
