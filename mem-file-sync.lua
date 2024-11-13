local log_file_path = "memory_access.log"
local max_log_size = 500 * 1024 * 1024  -- 50 MB
local frame_counter = 0
local delay_frames = 60  -- 65 seconds at 60 FPS

-- Attempt to open the log file for writing
local log_file = io.open(log_file_path, "w")
if log_file == nil then
    error(string.format("Failed to open log file at path: %s. Please check the path and permissions.", log_file_path))
end

local main_cpu = nil

-- Identify the CPU automatically
for device_name, device in pairs(manager.machine.devices) do
    if device_name:find("cpu") then
        main_cpu = device_name
        print(string.format("Using device: %s", main_cpu))  -- Print to console instead of logging to file
        break
    end
end

if main_cpu == nil then
    error("No CPU found for memory access")
end

-- Get the program memory space for the identified CPU
local mem_space = manager.machine.devices[main_cpu].spaces["program"]

if mem_space == nil then
    error(string.format("Program memory space for device %s not found", main_cpu))
end

-- Get the screen device to access the frame number
local screen = manager.machine.screens["screen"]
if screen == nil then
    error("No screen device found")
end

-- Function to write to the log and handle log rollover
local write_buffer = {}
local buffer_size = 5000  -- Buffer size for batching log writes

local function write_to_log(data)
    if log_file == nil then
        error("Log file is not open. Unable to write data.")
    end
    table.insert(write_buffer, data)
    if #write_buffer >= buffer_size then
        log_file:write(table.concat(write_buffer))
        write_buffer = {}  -- Clear buffer after writing
    end
    --if frame_counter % 6000 == 0 then
    log_file:flush()
    --end

    -- Check if the log file exceeds the maximum size and rotate if necessary
    local file_size = log_file:seek("end")
    if file_size > max_log_size then
        log_file:close()
        local backup_file_path = log_file_path .. ".backup"
        os.remove(backup_file_path)  -- Remove the old backup file if it exists
        os.rename(log_file_path, backup_file_path)  -- Rename current log file to backup
        log_file = io.open(log_file_path, "w")  -- Create a new log file
        if log_file == nil then
            error(string.format("Failed to open new log file at path: %s.", log_file_path))
        end
    end
end

-- Callback function for memory write
local function on_memory_write(address, value)
    local current_frame1 = screen:frame_number()
    write_to_log(string.format("frame,%d,write,%06X,value,%02X\n", current_frame1, address, value))
end

-- Callback function for memory read
local function on_memory_read(address, value)
    local current_frame1 = screen:frame_number()
    write_to_log(string.format("frame,%d,read,%06X,value,%02X\n", current_frame1, address, value))
end

-- Function to set memory taps
local function set_memory_taps()
    print("Setting memory read and write taps...")
    passthrough_read = mem_space:install_read_tap(0x000000, 0xFFFFFF, "reads", on_memory_read)
    passthrough_write = mem_space:install_write_tap(0x000000, 0xFFFFFF, "writes", on_memory_write)
end

set_memory_taps()

-- Register a frame done callback to manage log buffer flushes and reinstall taps if necessary
emu.register_frame_done(function()

    -- Skip processing if the emulator is paused
    if manager.machine.paused then
        return
    end

    -- Flush the buffer to the log file every frame
    if #write_buffer > 0 then
        log_file:write(table.concat(write_buffer))
        write_buffer = {}
    end
    
    -- Increment frame counter every frame
    frame_counter = frame_counter + 1

    -- Reinstall memory taps every 60 frames
    if frame_counter % 60 == 0 then
        set_memory_taps()
    end
end)
