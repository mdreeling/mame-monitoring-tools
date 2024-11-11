import tkinter as tk
import os
import colorsys

# Define parameters for memory representation
memory_size = 16 * 1024 * 1024  # 16 MB total memory
num_boxes = 10000  # Increase the number of boxes to 10000 for higher resolution
grid_size = 100  # Define grid size for 100x100 layout
canvas_width = 1010  # Add 5 pixels of padding on each side
canvas_height = 1010  # Add 5 pixels of padding on each side
box_size = memory_size // num_boxes

# Initialize global read and write counts for the entire memory size, not just num_boxes
# This assumes each "box" at the top level corresponds to a smaller chunk of the total memory size.
total_boxes = memory_size // box_size  # Determine total boxes for the entire memory range

global_read_counts = [0] * total_boxes
global_write_counts = [0] * total_boxes

# Initialize the main read_counts and write_counts for the initial viewable range
read_counts = global_read_counts[:num_boxes]
write_counts = global_write_counts[:num_boxes]

root = tk.Tk()

# Memory range label to show current section of memory
memory_range_label = tk.Label(root, text="Memory Range: 0x0 - 0xFFFFF")
memory_range_label.pack()

canvas = tk.Canvas(root, width=canvas_width, height=canvas_height + 100, bg="white")
canvas.pack()

# Function to update the memory range label
def update_memory_range_label(memory_start=None, memory_end=None):
    if memory_start is None or memory_end is None:
        memory_start = 0  # Default start
        memory_end = num_boxes * box_size - 1  # Default end
    memory_range_label.config(text=f"Memory Range: {hex(memory_start)} - {hex(memory_end)}")

# Create the Reset button
def reset_map():
    global read_counts, write_counts, box_size
    box_size = memory_size // num_boxes  # Reset box size to the original full range
    read_counts = [0] * num_boxes
    write_counts = [0] * num_boxes
    update_colors()
    update_memory_range_label()  # Update label after reset

reset_button = tk.Button(root, text="Reset Map", command=reset_map)
reset_button.pack()

# Initialize read and write counts for each box
read_counts = [0] * num_boxes
write_counts = [0] * num_boxes

# Initialize the current memory range for zoom
current_memory_start = 0
current_memory_end = memory_size - 1

# Initialize the Zoom Out button but keep it hidden initially
zoom_out_button = tk.Button(root, text="Zoom Out", command=lambda: zoom_out())
zoom_out_button.pack()
zoom_out_button.place_forget()  # Hide the button initially

# Function to zoom out and reset the view to the original memory range
def zoom_out():
    global current_memory_start, current_memory_end, box_size, read_counts, write_counts

    # Reset to the original memory range
    current_memory_start = 0
    current_memory_end = memory_size - 1
    box_size = memory_size // num_boxes

    # Update the main read_counts and write_counts to the full range
    read_counts = global_read_counts[:num_boxes]
    write_counts = global_write_counts[:num_boxes]

    # Hide the Zoom Out button
    zoom_out_button.place_forget()

    # Update the displayed memory range label
    update_memory_range_label(current_memory_start, current_memory_end)

    # Redraw the initial grid
    draw_initial_boxes()

# Update the zoom function to show the Zoom Out button when zooming in
def zoom_into_box(event):
    global box_size, current_memory_start, current_memory_end
    padding = 5
    col = (event.x - padding) // ((canvas_width - 2 * padding) // grid_size)
    row = (event.y - padding) // ((canvas_height - 2 * padding) // grid_size)
    box_index = row * grid_size + col
    
    if 0 <= box_index < num_boxes:
        # Calculate the memory range for the selected box within the current visible range
        memory_range = current_memory_end - current_memory_start + 1
        box_memory_size = memory_range // num_boxes

        # Determine the start and end of the new memory range based on the selected box
        new_memory_start = current_memory_start + (box_index * box_memory_size)
        new_memory_end = new_memory_start + box_memory_size - 1

        # Update global memory range for subsequent zooms
        current_memory_start, current_memory_end = new_memory_start, new_memory_end

        # Set new box size to reflect the zoomed-in range
        box_size = max((new_memory_end - new_memory_start + 1) // num_boxes, 1)

        # Update the displayed memory range label to focus on this box's range
        update_memory_range_label(new_memory_start, new_memory_end)

        # Update the read and write counts for the zoomed range
        update_zoomed_counts()

        # Redraw the grid based on the new memory range
        draw_initial_boxes()

        # Show the Zoom Out button after zooming in
        zoom_out_button.place(x=10, y=canvas_height + 50)

# Update read_counts and write_counts when zooming to the zoomed memory range
def update_zoomed_counts():
    global read_counts, write_counts
    # Calculate the range of indexes in the global counts array for the zoomed range
    start_index = int(current_memory_start / memory_size * len(global_read_counts))
    end_index = start_index + num_boxes

    # Slice and pad to ensure we have exactly num_boxes elements
    read_counts = global_read_counts[start_index:end_index]
    write_counts = global_write_counts[start_index:end_index]

    # If the sliced range is shorter than num_boxes, pad with zeros
    read_counts += [0] * (num_boxes - len(read_counts))
    write_counts += [0] * (num_boxes - len(write_counts))
# Initialize the Zoom Out button but keep it hidden initially
zoom_out_button = tk.Button(root, text="Zoom Out", command=lambda: zoom_out())
zoom_out_button.pack()
zoom_out_button.place_forget()  # Hide the button initially

# Function to zoom out and reset the view to the original memory range
def zoom_out():
    global current_memory_start, current_memory_end, box_size, read_counts, write_counts

    # Reset to the original memory range
    current_memory_start = 0
    current_memory_end = memory_size - 1
    box_size = memory_size // num_boxes

    # Update the main read_counts and write_counts to the full range
    read_counts = global_read_counts[:num_boxes]
    write_counts = global_write_counts[:num_boxes]

    # Hide the Zoom Out button
    zoom_out_button.place_forget()

    # Update the displayed memory range label
    update_memory_range_label(current_memory_start, current_memory_end)

    # Redraw the initial grid
    draw_initial_boxes()

# Update the zoom function to show the Zoom Out button when zooming in
def zoom_into_box(event):
    global box_size, current_memory_start, current_memory_end
    padding = 5
    col = (event.x - padding) // ((canvas_width - 2 * padding) // grid_size)
    row = (event.y - padding) // ((canvas_height - 2 * padding) // grid_size)
    box_index = row * grid_size + col
    
    if 0 <= box_index < num_boxes:
        # Calculate the memory range for the selected box within the current visible range
        memory_range = current_memory_end - current_memory_start + 1
        box_memory_size = memory_range // num_boxes

        # Determine the start and end of the new memory range based on the selected box
        new_memory_start = current_memory_start + (box_index * box_memory_size)
        new_memory_end = new_memory_start + box_memory_size - 1

        # Update global memory range for subsequent zooms
        current_memory_start, current_memory_end = new_memory_start, new_memory_end

        # Set new box size to reflect the zoomed-in range
        box_size = max((new_memory_end - new_memory_start + 1) // num_boxes, 1)

        # Update the displayed memory range label to focus on this box's range
        update_memory_range_label(new_memory_start, new_memory_end)

        # Update the read and write counts for the zoomed range
        update_zoomed_counts()

        # Redraw the grid based on the new memory range
        draw_initial_boxes()

        # Show the Zoom Out button after zooming in
        zoom_out_button.place(x=10, y=canvas_height + 50)


# Bind double-click event to zoom into the clicked box
canvas.bind("<Double-Button-1>", zoom_into_box)

# Draw initial boxes on the canvas and keep track of them by tags
box_tags = []

def draw_initial_boxes():
    canvas.delete("all")  # Clear existing boxes
    padding = 5  # 5 pixels of padding
    for i in range(num_boxes):
        row = i // grid_size
        col = i % grid_size
        x0 = padding + col * ((canvas_width - 2 * padding) // grid_size)
        x1 = padding + (col + 1) * ((canvas_width - 2 * padding) // grid_size)
        y0 = padding + row * ((canvas_height - 2 * padding) // grid_size)
        y1 = padding + (row + 1) * ((canvas_height - 2 * padding) // grid_size)
        tag = f"box_{i}"
        canvas.create_rectangle(x0, y0, x1, y1, outline="lightgray", fill="white", tags=tag)
        box_tags.append(tag)

draw_initial_boxes()
update_memory_range_label()  # Initialize label

# Remaining code for legend, box color updating, hover events, and log monitoring continues as before.


# Draw legend
def draw_legend():
    legend_x = 10
    legend_y = canvas_height + 10
    legend_spacing = 20
    
    canvas.create_text(legend_x, legend_y, anchor="nw", text="Legend:", font=("Arial", 10, "bold"))
    
    # Light blue to dark blue gradient for reads only
    canvas.create_rectangle(legend_x, legend_y + legend_spacing, legend_x + 15, legend_y + legend_spacing + 15, fill="#add8e6", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + legend_spacing, anchor="nw", text="Reads Only (Low)", font=("Arial", 10))
    canvas.create_rectangle(legend_x, legend_y + 2 * legend_spacing, legend_x + 15, legend_y + 2 * legend_spacing + 15, fill="#00008b", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + 2 * legend_spacing, anchor="nw", text="Reads Only (High)", font=("Arial", 10))
    
    # Light green to dark green gradient for writes only
    canvas.create_rectangle(legend_x, legend_y + 3 * legend_spacing, legend_x + 15, legend_y + 3 * legend_spacing + 15, fill="#90ee90", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + 3 * legend_spacing, anchor="nw", text="Writes Only (Low)", font=("Arial", 10))
    canvas.create_rectangle(legend_x, legend_y + 4 * legend_spacing, legend_x + 15, legend_y + 4 * legend_spacing + 15, fill="#006400", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + 4 * legend_spacing, anchor="nw", text="Writes Only (High)", font=("Arial", 10))
    
    # Yellow to red gradient for reads and writes
    canvas.create_rectangle(legend_x, legend_y + 5 * legend_spacing, legend_x + 15, legend_y + 5 * legend_spacing + 15, fill="#ffff00", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + 5 * legend_spacing, anchor="nw", text="Reads and Writes (Low)", font=("Arial", 10))
    canvas.create_rectangle(legend_x, legend_y + 6 * legend_spacing, legend_x + 15, legend_y + 6 * legend_spacing + 15, fill="#ff0000", outline="lightgray")
    canvas.create_text(legend_x + 20, legend_y + 6 * legend_spacing, anchor="nw", text="Reads and Writes (High)", font=("Arial", 10))

draw_legend()

# Function to update the color of a box based on read/write counts
def update_box_color(index, max_accesses):
    read_count = read_counts[index]
    write_count = write_counts[index]
    total_accesses = read_count + write_count

    if total_accesses == 0:
        color = "white"
    elif read_count > 0 and write_count == 0:
        # Light blue to dark blue gradient for reads only
        ratio = min(read_count / max_accesses, 1)  # Normalize ratio to be between 0 and 1
        r = int((173 * (1 - ratio)) + (0 * ratio))
        g = int((216 * (1 - ratio)) + (0 * ratio))
        b = int((230 * (1 - ratio)) + (139 * ratio))
        color = f"#{r:02x}{g:02x}{b:02x}"
    elif write_count > 0 and read_count == 0:
        # Light green to dark green gradient for writes only
        ratio = min(write_count / max_accesses, 1)  # Normalize ratio to be between 0 and 1
        r = int((144 * (1 - ratio)) + (0 * ratio))
        g = int((238 * (1 - ratio)) + (100 * ratio))
        b = int((144 * (1 - ratio)) + (0 * ratio))
        color = f"#{r:02x}{g:02x}{b:02x}"
    else:
        # Calculate color gradient from yellow to red based on total accesses relative to max_accesses
        ratio = min(total_accesses / max_accesses, 1)  # Normalize ratio to be between 0 and 1
        hue = (1 - ratio) * 0.15  # Yellow to red in HSV
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    # Update the color of the existing rectangle
    canvas.itemconfig(box_tags[index], fill=color)

# Display memory information when hovering over a box
def on_hover(event):
    padding = 5
    col = (event.x - padding) // ((canvas_width - 2 * padding) // grid_size)
    row = (event.y - padding) // ((canvas_height - 2 * padding) // grid_size)
    box_index = row * grid_size + col
    
    if 0 <= box_index < num_boxes:  # Ensure box_index is within bounds
        # Calculate the memory range for the current box in the zoomed range
        memory_range_start = current_memory_start + box_index * box_size
        memory_range_end = memory_range_start + box_size - 1
        
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
    max_accesses = max(read_counts[i] + write_counts[i] for i in range(num_boxes))
    if max_accesses == 0:
        max_accesses = 1  # Avoid division by zero
    for i in range(num_boxes):
        update_box_color(i, max_accesses)
    canvas.update()

# Adjust monitor_log to check the bounds of the current counts
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
                        if not line.startswith("read") and not line.startswith("write"):
                            continue

                        # Split the line into expected parts
                        access_type, address_hex, _, value_hex = line.split(',')
                        address = int(address_hex, 16)
                        box_index = (address - current_memory_start) // box_size

                        if 0 <= box_index < num_boxes:
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