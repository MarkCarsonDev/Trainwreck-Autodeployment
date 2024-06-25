import time
from datetime import datetime

# Define the file path in the script's directory
file_path = 'current_time.txt'

def write_current_time():
    # Get the current date and time
    now = datetime.now()
    # Format the date and time in an easy to read format
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Write (or overwrite) the formatted time to the file
    with open(file_path, 'w') as file:
        file.write(formatted_time)
    print(f"Current time written to {file_path}: {formatted_time}")

def main():
    write_current_time()
    # Wait for 1 minute (60 seconds)
    time.sleep(60)

if __name__ == "__main__":
    main()
