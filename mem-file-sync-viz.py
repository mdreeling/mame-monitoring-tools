import matplotlib.pyplot as plt
import numpy as np
import time
import os

# Define parameters for memory representation
memory_size = 16 * 1024 * 1024  # 16 MB total memory
block_size = 256  # Each row represents 256 bytes (256 columns)

# Calculate the number of rows for the memory grid
num_rows = memory_size // block_size

# Initialize heatmaps to track reads and writes to the memory space
read_heatmap = np.zeros((num_rows, block_size), dtype=np.uint32)
write_heatmap = np.zeros((num_rows, block_size), dtype=np.uint32)

# Create the figure for dynamic updating
plt.ion()  # Interactive mode on
fig, ax = plt.subplots(figsize=(16, 9))
plt.xlabel('Memory Offset within Row (0-255)')
plt.ylabel('Base Memory Address (Row)')
plt.title('Dynamic Memory Read/Write Heatmap')

# Function to update the memory access plot
def update_memory_access_plot(read_heatmap, write_heatmap, ax):
    ax.clear()
    plt.xlabel('Memory Offset within Row (0-255)')
    plt.ylabel('Base Memory Address (Row)')
    plt.title('Dynamic Memory Read/Write Heatmap')

    # Find all non-zero entries in the heatmaps to plot them
    read_rows, read_cols = np.where(read_heatmap > 0)
    write_rows, write_cols = np.where(write_heatmap > 0)

    # Plot reads as green dots
    ax.scatter(read_cols, read_rows, c='green', s=10, alpha=0.5, label='Reads')
    # Plot writes as red dots
    ax.scatter(write_cols, write_rows, c='red', s=50, alpha=0.7, label='Writes')

    # Set axis limits
    ax.set_xlim(-0.5, block_size - 0.5)
    ax.set_ylim(-0.5, num_rows - 0.5)

    plt.legend()
    plt.draw()
    plt.pause(0.1)

# Monitor the memory access log file for changes with roll-over detection
log_file_path = "..\..\mame\memory_access.log"
last_read_position = 0

while True:
    if os.path.exists(log_file_path):
        file_size = os.path.getsize(log_file_path)

        # Handle file rollover by checking if the current read position exceeds the file size
        if last_read_position > file_size:
            print("Log rollover detected, resetting read position.")
            last_read_position = 0

        with open(log_file_path, "r") as log_file:
            log_file.seek(last_read_position)  # Start from where we left off
            for line in log_file:
                line = line.strip()
                if line:
                    # Print every line being read from the log file to see what's being read
                    print(f"Reading line: {line}")
                    try:
                        # Adjusted to ignore lines that don't match the expected format
                        if not line.startswith("read") and not line.startswith("write"):
                            continue

                        # Split the line into expected parts
                        access_type, address_hex, _, value_hex = line.split(',')
                        address = int(address_hex, 16)
                        
                        # Calculate the row and column for the heatmap
                        row = address // block_size
                        col = address % block_size
                        
                        if row < num_rows and col < block_size:
                            if access_type == 'read':
                                # Increment the value in the heatmap to indicate a read occurred
                                read_heatmap[row, col] += 1
                            elif access_type == 'write':
                                # Increment the value in the heatmap to indicate a write occurred
                                write_heatmap[row, col] += 1
                            
                            # Debug output to verify processing
                            print(f"Processed {access_type} at address {address_hex} (row {row}, col {col}) with value {value_hex}")
                    except ValueError as e:
                        print(f"Error processing line '{line}': {e}")
            last_read_position = log_file.tell()  # Update the position for the next read

    # Update the plot with the new heatmap data
    update_memory_access_plot(read_heatmap, write_heatmap, ax)
    time.sleep(0.5)  # Short delay to allow visualization updates
