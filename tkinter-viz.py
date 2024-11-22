import tkinter as tk
import os
import colorsys
import time

from PIL import Image, ImageTk


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

# Placeholder for the image widget
frame_image_label = tk.Label(root)
frame_image_label.pack(side="right")

# Add a Scrollbar for horizontal scrolling
instructions_scrollbar = tk.Scrollbar(root, orient="horizontal")
instructions_scrollbar.pack(side="bottom", fill="x")

# Add the Text widget for instructions with a scrollbar
frame_instructions_text = tk.Text(
    root,
    width=70,  # Adjust width to fit your needs
    height=40,  # Adjust height to fit your needs
    wrap="none",  # Prevent text wrapping
    font=("Courier", 10),  # Use monospaced font for alignment
    xscrollcommand=instructions_scrollbar.set
)
frame_instructions_text.pack(side="right", padx=10)

# Configure the scrollbar to work with the Text widget
instructions_scrollbar.config(command=frame_instructions_text.xview)

# Add a Text widget for displaying the diff results
frame_diff_text = tk.Text(
    root,
    width=70,  # Adjust width to fit your needs
    height=40,  # Adjust height to fit your needs
    wrap="none",  # Prevent text wrapping
    font=("Courier", 10)  # Use monospaced font for alignment
)
frame_diff_text.pack(side="right", padx=10)

# Add a Label widget for displaying changed registers
#registers_label = tk.Label(root, text="Changed Registers:", font=("Courier", 10), anchor="w", justify="left")
#registers_label.pack(side="top", padx=10, pady=5)

canvas = tk.Canvas(root, width=canvas_width, height=canvas_height + 100, bg="white")
canvas.pack()

def extract_registers(instruction_lines):
    """Extract register values from the instruction lines."""
    registers = {}
    for line in instruction_lines:
        if "--" in line:
            parts = line.split("--")[0].split()  # Take the part before the "--"
            for part in parts:
                if "=" in part:
                    reg, value = part.split("=")
                    if reg.startswith("D") or reg.startswith("A") or reg == "PC":
                        registers[reg] = value.strip()
    return registers

def diff_registers(prev_registers, curr_registers):
    """Compare registers between frames and return the changed ones."""
    changed_registers = {}
    for reg, curr_value in curr_registers.items():
        prev_value = prev_registers.get(reg)
        if prev_value != curr_value:
            changed_registers[reg] = (prev_value, curr_value)  # Store previous and current values
    return changed_registers

def preprocess_instructions(instruction_lines):
    """Preprocess instruction lines: remove 'frame=####' and extract instructions after '--'."""
    processed_instructions = []
    for line_number, line in enumerate(instruction_lines, start=1):
        if "--" in line:
            try:
                # Split on '--' and take the part after it
                _, instruction = line.split("--", 1)
                processed_instructions.append((line_number, instruction.strip()))
            except ValueError:
                continue  # Skip lines that don't conform to the expected format
    return processed_instructions

def diff_instructions(prev_instructions, curr_instructions):
    """Diff two sets of instructions and return new instructions."""
    # Extract only the instruction strings for comparison
    prev_set = {instr for _, instr in prev_instructions}
    new_instructions = [(line_number, instr) for line_number, instr in curr_instructions if instr not in prev_set]
    return new_instructions

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
    update_box_colors()
    update_memory_range_label()  # Update label after reset

reset_button = tk.Button(root, text="Reset Map", command=reset_map)
reset_button.pack()

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

# Bind double-click event to zoom into the clicked box
canvas.bind("<Double-Button-1>", zoom_into_box)

# Draw initial boxes on the canvas and keep track of them by tags
box_tags = []

def draw_initial_boxes():
    print("drawing initial boxes")
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
current_colors = ["white"] * num_boxes

# For flashing indicators
prev_read_counts = [0] * num_boxes
prev_write_counts = [0] * num_boxes
threshold = 1  # Number of reads/writes to trigger flashing

def precompute_gradients():
    max_steps = 100  # Define a reasonable number of gradient levels
    read_colors = []
    write_colors = []
    for i in range(max_steps):
        ratio = i / (max_steps - 1)
        # Precompute read-only colors (light blue to dark blue)
        r = int((173 * (1 - ratio)) + (0 * ratio))
        g = int((216 * (1 - ratio)) + (0 * ratio))
        b = int((230 * (1 - ratio)) + (139 * ratio))
        read_colors.append(f"#{r:02x}{g:02x}{b:02x}")

        # Precompute write-only colors (light green to dark green)
        r = int((144 * (1 - ratio)) + (0 * ratio))
        g = int((238 * (1 - ratio)) + (100 * ratio))
        b = int((144 * (1 - ratio)) + (0 * ratio))
        write_colors.append(f"#{r:02x}{g:02x}{b:02x}")

    return read_colors, write_colors

read_gradient, write_gradient = precompute_gradients()

def update_box_colors():
    max_accesses = max(read_counts[i] + write_counts[i] for i in range(num_boxes))
    if max_accesses == 0:
        max_accesses = 1  # Avoid division by zero

    update_operations = []
    for i in range(num_boxes):
        read_count = read_counts[i]
        write_count = write_counts[i]
        total_accesses = read_count + write_count

        max_steps = 100
        if total_accesses == 0:
            color = "white"
        elif read_count > 0 and write_count == 0:
            ratio_index = min(int((read_count / max_accesses) * (max_steps - 1)), max_steps - 1)
            color = read_gradient[ratio_index]
        elif write_count > 0 and read_count == 0:
            ratio_index = min(int((write_count / max_accesses) * (max_steps - 1)), max_steps - 1)
            color = write_gradient[ratio_index]
        else:
            ratio = min(total_accesses / max_accesses, 1)
            hue = (1 - ratio) * 0.15
            r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
            color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

        # Batch updates to reduce individual itemconfig calls
        if current_colors[i] != color:
            update_operations.append((box_tags[i], color))
            current_colors[i] = color

        # Calculate read/write difference for flashing
        read_diff = read_counts[i] - prev_read_counts[i]
        write_diff = write_counts[i] - prev_write_counts[i]

        # Update the previous counts for the next cycle
        prev_read_counts[i] = read_count
        prev_write_counts[i] = write_count

        if read_diff > threshold or write_diff > threshold:
            flash_x(i)

    for tag, color in update_operations:
        canvas.itemconfig(tag, fill=color)

    canvas.update()  # Finally update the canvas

def flash_x(index):
    # Determine the coordinates for the box
    row = index // grid_size
    col = index % grid_size
    padding = 5
    box_width = (canvas_width - 2 * padding) // grid_size
    box_height = (canvas_height - 2 * padding) // grid_size
    x0 = padding + col * box_width
    y0 = padding + row * box_height
    x1 = x0 + box_width
    y1 = y0 + box_height

    # Draw the yellow "X"
    x_tag = f"flash_x_{index}"
    line1 = canvas.create_line(x0, y0, x1, y1, fill="yellow", width=2, tags=x_tag)
    line2 = canvas.create_line(x0, y1, x1, y0, fill="yellow", width=2, tags=x_tag)

    # Remove the "X" after a short delay to create a flashing effect
    canvas.after(300, lambda: canvas.delete(x_tag))


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

# Frame-by-frame mode implementation
# Track frame-specific memory access data and add a toggle button and slider

# Frame data to track specific frame memory accesses
frame_data = {}  # Dictionary to store read/write counts per frame for frame-by-frame mode

# Frame-by-frame mode state
frame_by_frame_mode = False
current_frame = 0
max_frame = 0

# Frame-by-frame slider
frame_slider = tk.Scale(root, from_=0, to=0, orient="horizontal", label="Frame", command=lambda val: show_frame(int(val)))
frame_slider.pack_forget()  # Hide initially

continue_monitoring = True

# Button to toggle frame-by-frame mode
def toggle_frame_by_frame_mode():
    global frame_by_frame_mode, continue_monitoring
    frame_by_frame_mode = not frame_by_frame_mode
    
    if frame_by_frame_mode:
        # Stop monitoring the file and show the slider
        frame_slider.pack()
        frame_slider.config(to=max_frame)
        continue_monitoring = False  # Stop continuous monitoring
        print("Stopping and moving to Frame-By-Frame mode")
    else:
        # Hide the slider and resume normal mode
        frame_slider.pack_forget()
        continue_monitoring = True  # Resume continuous monitoring
        print("Resuming reading memory activity...")

frame_by_frame_button = tk.Button(root, text="Frame by Frame Mode", command=toggle_frame_by_frame_mode)
frame_by_frame_button.pack()

# Global flag to indicate if show_frame is already running
frame_rendering_in_progress = False

def dump_debug_instructions(frame, prev_instructions, curr_instructions):
    """Dump current and previous instructions to debug files."""
    try:
        # Write current instructions to a debug file
        current_debug_path = f"slide-debug-{frame:05d}-current.txt"
        with open(current_debug_path, "w") as curr_debug_file:
            curr_debug_file.write("\n".join(f"{instr}" for line_number, instr in curr_instructions))
        print(f"Current instructions dumped to {current_debug_path}")

        # Write previous instructions to a debug file
        previous_debug_path = f"slide-debug-{frame:05d}-previous.txt"
        with open(previous_debug_path, "w") as prev_debug_file:
            prev_debug_file.write("\n".join(f"{instr}" for line_number, instr in prev_instructions))
        print(f"Previous instructions dumped to {previous_debug_path}")
    except Exception as e:
        print(f"Error dumping debug instructions for frame {frame}: {e}")

# Function to show a specific frame with a debounce mechanism
def show_frame(frame):
    global read_counts, write_counts, frame_rendering_in_progress

    if frame_rendering_in_progress:
        print(f"Skipping frame {frame}, rendering is already in progress.")
        return  # Skip if already rendering

    # Set flag to indicate rendering is in progress
    frame_rendering_in_progress = True

    start_time = time.time()  # Start timing the function
    if frame in frame_data:
        read_counts, write_counts = frame_data[frame]
        update_box_colors()

    # Load and display the PNG for the current frame
    try:
        frame_image_path = f"../../mame/snap/frames/{frame:05d}.png"
        img = Image.open(frame_image_path)

        # Calculate the new size while maintaining the aspect ratio
        original_width, original_height = 384, 224
        aspect_ratio = original_width / original_height

        target_width = canvas_width
        target_height = int(target_width / aspect_ratio)

        if target_height > canvas_height:
            target_height = canvas_height
            target_width = int(target_height * aspect_ratio)

        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Convert to a Tkinter-compatible image
        img_tk = ImageTk.PhotoImage(img)

        # Update the image label
        frame_image_label.config(image=img_tk)
        frame_image_label.image = img_tk  # Keep a reference to avoid garbage collection
    except FileNotFoundError:
        print(f"Frame image not found: {frame_image_path}")
    except Exception as e:
        print(f"Error displaying frame image: {e}")


    # Load and display the instructions for the current frame
    try:
        instructions_file_path = f"../../mame/instructions/{frame}.log"
        with open(instructions_file_path, "r") as instructions_file:
            instructions = instructions_file.read()

        # Update the text widget with the instructions
        frame_instructions_text.delete("1.0", tk.END)  # Clear previous contents
        frame_instructions_text.insert(tk.END, instructions)  # Insert new instructions
    except FileNotFoundError:
        print(f"Instructions file not found: {instructions_file_path}")
        frame_instructions_text.delete("1.0", tk.END)
        frame_instructions_text.insert(tk.END, "No instructions available for this frame.")
    except Exception as e:
        print(f"Error loading instructions: {e}")

        # Load and preprocess the current and previous frame's instructions
    try:
        # Load and preprocess the current and previous frame's instructions
        current_frame_path = f"../../mame/instructions/{frame}.log"
        with open(current_frame_path, "r") as curr_file:
            current_instructions = curr_file.readlines()
            current_registers = extract_registers(current_instructions)

        previous_frame_path = f"../../mame/instructions/{frame - 1}.log"
        previous_instructions = []
        previous_registers = {}
        try:
            with open(previous_frame_path, "r") as prev_file:
                previous_instructions = prev_file.readlines()
                previous_registers = extract_registers(previous_instructions)
        except FileNotFoundError:
            pass  # If no previous frame exists, assume it's the first frame

        # Dump debug files for the current and previous instructions
        dump_debug_instructions(frame, previous_instructions, current_instructions)

        # Perform the diff to get new instructions
        new_instructions = diff_instructions(
            preprocess_instructions(previous_instructions),
            preprocess_instructions(current_instructions),
        )

        # Perform the diff to get changed registers
        changed_registers = diff_registers(previous_registers, current_registers)

        # Update the registers Label widget
        if changed_registers:
            registers_output = "\n".join(
                f"{reg}: {prev} → {curr}"
                for reg, (prev, curr) in changed_registers.items()
            )
        else:
            registers_output = "No registers changed in this frame."

        #registers_label.config(text=f"Changed Registers:\n{registers_output}")

        # Update the diff Text widget
        frame_diff_text.delete("1.0", tk.END)  # Clear previous contents
        if new_instructions:
            diff_output = "\n".join(f"Line {line_number}: {instr}" for line_number, instr in new_instructions)
            frame_diff_text.insert(tk.END, diff_output)
        else:
            frame_diff_text.insert(tk.END, "No new instructions in this frame.")
    except FileNotFoundError as e:
        print(f"Error loading instructions for frame {frame}: {e}")
        frame_diff_text.delete("1.0", tk.END)
        frame_diff_text.insert(tk.END, "Instructions not found for the current frame.")
    except Exception as e:
        print(f"Error processing diff: {e}")
        frame_diff_text.delete("1.0", tk.END)
        frame_diff_text.insert(tk.END, "Error processing instructions diff.")
    # Clear the flag after rendering is done
    frame_rendering_in_progress = False

    end_time = time.time()  # End timing the function
    print(f"Execution time for show_frame({frame}): {end_time - start_time:.4f} seconds")


# Function to monitor the log file for memory accesses and update frame information
# noinspection PyTypeChecker
def monitor_log():
    global read_counts, write_counts, last_read_position, current_frame, current_frame_operations, max_frame, continue_monitoring
    if continue_monitoring:
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
                        parts = line.split(',')

                        # Only parse lines with exactly 6 parts
                        if len(parts) == 7:
                            try:
                                # Extract frame, access type, address, and value
                                new_frame = int(parts[0])  # Frame number is always present
                                access_type = parts[1]
                                address_hex = parts[2]
                                value_hex = parts[3]

                                if current_frame == 0:
                                    frame_slider.config(from_=new_frame)
                                # Track frame-specific data for frame-by-frame mode
                                if new_frame != current_frame:
                                    # Store the current frame data before switching to the new frame
                                    frame_data[current_frame] = (read_counts[:], write_counts[:])
                                    current_frame = new_frame
                                    max_frame = max(max_frame, new_frame)
                                    frame_slider.config(to=max_frame)

                                if not continue_monitoring:
                                    # Reset read and write counts for the new frame
                                    read_counts = [0] * num_boxes
                                    write_counts = [0] * num_boxes


                                # Process the memory access event
                                address = int(address_hex, 16)
                                value = int(value_hex, 16)
                                box_index = (address - current_memory_start) // box_size

                                if 0 <= box_index < num_boxes:
                                    if access_type == 'R':
                                        read_counts[box_index] += 1
                                    elif access_type == 'W':
                                        write_counts[box_index] += 1

                            except ValueError as e:
                                print(f"Error processing line '{line}': {e}")

                last_read_position = log_file.tell()  # Update the position for the next read
                print("Visualization is up to date with the end of the file.")

        # Update colors for the continuous mode
        update_box_colors()

        # Schedule the next log check
    root.after(update_interval, lambda: monitor_log())

# Run the Tkinter main loop
monitor_log()
root.mainloop()