import tkinter as tk
import os
import time

# Define parameters for memory representation
memory_size = 16 * 1024 * 1024  # 16 MB total memory
num_boxes = 100  # Divide the memory map into 100 boxes
box_size = memory_size // num_boxes

# Initialize read and write counts for each box
read_counts = [0] * num_boxes
write_counts = [0] * num_boxes

# Create the Tkinter window
root = tk.Tk()
root.title("Memory Access Heatmap")
canvas = tk.Canvas(root, width=1000, height=500, bg="white")
canvas.pack()

# Draw initial boxes on the canvas
def draw_initial_boxes():
    for i in range(num_boxes):
        x0 = i * (1000 // num_boxes)
        x1 = (i + 1) * (1000 // num_boxes)
        y0 = 0
        y1 = 500
        canvas.create_rectangle(x0, y0, x1, y1, outline="black", fill="white", tags=f"box_{i}")

draw_initial_boxes()

# Update the boxes with read/write colors temporarily
def flash_box(index, color, duration=0.1):
    x0 = index * (1000 // num_boxes)
    x1 = (index + 1) * (1000 // num_boxes)
    if color == 'yellow':
        canvas.create_rectangle(x0, 0, x1, 250, outline="black", fill=color, tags=f"box_{index}")
    elif color == 'green':
        canvas.create_rectangle(x0, 250, x1, 500, outline="black", fill=color, tags=f"box_{index}")
    #canvas.update()
    #root.after(int(duration * 1000), lambda: reset_box(index))

def reset_box(index):
    x0 = index * (1000 // num_boxes)
    x1 = (index + 1) * (1000 // num_boxes)
    canvas.create_rectangle(x0, 0, x1, 500, outline="black", fill="white", tags=f"box_{index}")
    canvas.update()

# Monitor the memory access log file for changes with roll-over detection
log_file_path = "..\..\mame\memory_access.log"
last_read_position = 0
update_interval = 0.0001  # Configurable update interval in seconds

while True:
    if os.path.exists(log_file_path):
        file_size = os.path.getsize(log_file_path)

        # Handle file rollover by checking if the current read position exceeds the file size
        if last_read_position > file_size:
            print("Log rollover detected, resetting read position.")
            last_read_position = 0

        with open(log_file_path, "r") as log_file:
            log_file.seek(last_read_position)  # Start from where we left off
            line_count = 0
            boxes_to_flash = []
            for line in log_file:
                line = line.strip()
                if line:
                    # Print every line being read from the log file to see what's being read
                    line_count += 1
                    if line_count % 1000 == 0:
                        for index, color in boxes_to_flash:
                            flash_box(index, color)
                        canvas.update()
                        boxes_to_flash.clear()
                        print(f"Processed {line_count} lines so far.")
                    #print(f"Reading line: {line}")
                    try:
                        # Adjusted to ignore lines that don't match the expected format
                        if not line.startswith("read") and not line.startswith("write"):
                            continue

                        # Split the line into expected parts
                        access_type, address_hex, _, value_hex = line.split(',')
                        address = int(address_hex, 16)
                        box_index = address // box_size

                        if box_index < num_boxes:
                            if access_type == 'read':
                                boxes_to_flash.append((box_index, 'green'))
                            elif access_type == 'write':
                                boxes_to_flash.append((box_index, 'yellow'))

                            # Debug output to verify processing
                            #print(f"Processed {access_type} at address {address_hex} (box {box_index}) with value {value_hex}")
                    except ValueError as e:
                        print(f"Error processing line '{line}': {e}")
            last_read_position = log_file.tell()  # Update the position for the next read
            print("Visualization is up to date with the end of the file.")

    if len(boxes_to_flash) > 0:
        for index, color in boxes_to_flash:
            flash_box(index, color)
        canvas.update()
        boxes_to_flash.clear()
    time.sleep(update_interval)  # Configurable delay for visualization updates
