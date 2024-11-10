local log_file_path = "memory_access.log"
local max_log_size = 1 * 1024 * 1024 * 1024  -- 1 GB

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

log_file:flush()

-- Get the program memory space for the identified CPU
local mem_space = manager.machine.devices[main_cpu].spaces["program"]

if mem_space == nil then
    error(string.format("Program memory space for device %s not found", main_cpu))
end

-- Function to write to the log and handle log rollover
local function write_to_log(data)
    if log_file == nil then
        error("Log file is not open. Unable to write data.")
    end
    log_file:write(data)
    log_file:flush()
end

-- Callback function for memory write
local function on_memory_write(address, value)
    write_to_log(string.format("write,%06X,value,%02X\n", address, value))
end
-- Callback function for memory write
local function on_memory_read(address, value)
    write_to_log(string.format("read,%06X,value,%02X\n", address, value))
end

-- Set watchpoints on the entire address range (adjust the range as needed)
--for address = 0, 0xFFFFFF do  -- Entire 16MB address range
mem_space:install_write_tap(0x000000, 0xFFFFFF, "writes", on_memory_write)
mem_space:install_read_tap(0x000000, 0xFFFFFF, "reads", on_memory_read)
--end

-- Register a function to check log size and handle rollover at each frame
emu.register_frame_done(function()
    -- Handle log rollover if file size exceeds limit
    local file_size = log_file:seek("end")  -- Get the current file size
    if file_size >= max_log_size then
        log_file:close()  -- Close the current log file
        log_file = io.open(log_file_path, "w")  -- Reopen it to start from scratch
        if log_file == nil then
            error(string.format("Failed to reopen log file at path: %s. Please check the path and permissions.", log_file_path))
        end
        log_file:write("-- Log rollover occurred --\n")  -- Mark the rollover in the log
        log_file:flush()  -- Ensure the message is written immediately
    end
end)
