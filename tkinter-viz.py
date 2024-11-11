import tkinter as tk
import os
import colorsys

# Define parameters for memory representation
memory_size = 16 * 1024 * 1024  # 16 MB total memory
num_boxes = 500  # Divide the memory map into 500 boxes
grid_size = 25  # Define grid size for 25x20 layout
canvas_width = 1000
canvas_height = 1000
box_size = memory_size // num_boxes

# Initialize read and write counts for each box
read_counts = [0] * num_boxes
write_counts = [0] * num_boxes

# Create the Tkinter window
root = tk.Tk()
root.title("Memory Access Heatmap")
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.pack()

# Draw initial boxes on the canvas
def draw_initial_boxes():
    for i in range(num_boxes):
        row = i // grid_size
        col = i % grid_size
        x0 = col * (canvas_width // grid_size)
        x1 = (col + 1) * (canvas_width // grid_size)
        y0 = row * (canvas_height // (num_boxes // grid_size))
        y1 = (row + 1) * (canvas_height // (num_boxes // grid_size))
        canvas.create_rectangle(x0, y0, x1, y1, outline="black", fill="white", tags=f"box_{i}")

draw_initial_boxes()

# Update the color of a box based on read/write counts
def update_box_color(index):
    total_accesses = read_counts[index] + write_counts[index]
    if total_accesses == 0:
        color = "white"
    else:
        # Calculate color gradient from yellow to red based on total accesses
        ratio = min(total_accesses / 100000, 1)  # Normalize ratio to be between 0 and 1
        hue = (1 - ratio) * 0.15  # Yellow to red in HSV
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    row = index // grid_size
    col = index % grid_size
    x0 = col * (canvas_width // grid_size)
    x1 = (col + 1) * (canvas_width // grid_size)
    y0 = row * (canvas_height // (num_boxes // grid_size))
    y1 = (row + 1) * (canvas_height // (num_boxes // grid_size))
    canvas.create_rectangle(x0, y0, x1, y1, outline="black", fill=color, tags=f"box_{index}")

# Display memory information when hovering over a box
def on_hover(event):
    col = event.x // (canvas_width // grid_size)
    row = event.y // (canvas_height // (num_boxes // grid_size))
    box_index = row * grid_size + col
    if 0 <= box_index < num_boxes:
        memory_range_start = box_index * box_size
        memory_range_end = (box_index + 1) * box_size - 1
        read_count = read_counts[box_index]
        write_count = write_counts[box_index]
        info_text = (f"Memory Range: {hex(memory_range_start)} - {hex(memory_range_end)}\n"
                     f"Reads: {read_count}, Writes: {write_count}")
        canvas.delete("hover_text")
        canvas.create_text(event.x, event.y, text=info_text, anchor="nw", tags="hover_text", fill="black")

# Clear hover information when the mouse leaves the canvas
def on_leave(event):
    canvas.delete("hover_text")

canvas.bind("<Motion>", on_hover)
canvas.bind("<Leave>", on_leave)

# Monitor the memory access log file for changes with roll-over detection
log_file_path = "../../mame/memory_access.log"
last_read_position = 0
update_interval = 100  # Configurable update interval in milliseconds

# Cache colors for reuse
gradient_cache = {}

# Optimized update function to reduce canvas redraw frequency
def update_colors():
    for i in range(num_boxes):
        total_accesses = read_counts[i] + write_counts[i]
        if total_accesses == 0:
            color = "white"
        else:
            # Use cached color if available
            if total_accesses in gradient_cache:
                color = gradient_cache[total_accesses]
            else:
                # Calculate color gradient from yellow to red based on total accesses
                ratio = min(total_accesses / 100000, 1)  # Normalize ratio to be between 0 and 1
                hue = (1 - ratio) * 0.15  # Yellow to red in HSV
                r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
                color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
                gradient_cache[total_accesses] = color

        row = i // grid_size
        col = i % grid_size
        x0 = col * (canvas_width // grid_size)
        x1 = (col + 1) * (canvas_width // grid_size)
        y0 = row * (canvas_height // (num_boxes // grid_size))
        y1 = (row + 1) * (canvas_height // (num_boxes // grid_size))
        canvas.create_rectangle(x0, y0, x1, y1, outline="black", fill=color, tags=f"box_{i}")
    canvas.update()

def monitor_log():
    global last_read_position
    if os.path.exists(log_file_path):
        file_size = os.path.getsize(log_file_path)

        # Handle file rollover by checking if the current read position exceeds the file size
        if last_read_position > file_size:
            print("Log rollover detected, resetting read position.")
            last_read_position = 0

        with open(log_file_path, "r") as log_file:
            log_file.seek(last_read_position)  # Start from where we left off
            line_count = 0
            for line in log_file:
                line = line.strip()
                if line:
                    # Increment line count and print every 1000 lines processed
                    line_count += 1
                    if line_count % 1000 == 0:
                        print(f"Processed {line_count} lines so far.")

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
                                read_counts[box_index] += 1
                            elif access_type == 'write':
                                write_counts[box_index] += 1

                    except ValueError as e:
                        print(f"Error processing line '{line}': {e}")
            last_read_position = log_file.tell()  # Update the position for the next read
            print("Visualization is up to date with the end of the file.")

    # Update all box colors at once to reduce canvas update frequency
    update_colors()

    # Schedule the next log check
    root.after(update_interval, monitor_log)

# Start monitoring the log
monitor_log()

# Run the Tkinter main loop
root.mainloop()
