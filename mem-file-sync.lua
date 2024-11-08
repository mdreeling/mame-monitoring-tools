local log_file_path = "memory_access.log"
local max_log_size = 1 * 1024 * 1024 * 1024  -- 1 GB
local log_file = io.open(log_file_path, "w")
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
    log_file:write(data)
    log_file:flush()
end

local current_address = 0x000000
local max_address = 0x00FFFF  -- Define the end of the range you want to monitor

-- Register a function to poll memory addresses at each frame
emu.register_frame_done(function()
    -- Poll a range of memory addresses dynamically
    for _ = 1, 10 do  -- Sample 10 different addresses per frame for better coverage
        local value = mem_space:read_u8(current_address)
        write_to_log(string.format("read,%06X,value,%02X\n", current_address, value))

        current_address = current_address + 1
        if current_address > max_address then
            current_address = 0x000000  -- Reset to the beginning of the range if we reach the end
        end
    end

    -- Handle log rollover if file size exceeds limit
    local file_size = log_file:seek("end")  -- Get the current file size
    if file_size >= max_log_size then
        log_file:close()  -- Close the current log file
        log_file = io.open(log_file_path, "w")  -- Reopen it to start from scratch
        log_file:write("-- Log rollover occurred --\n")  -- Mark the rollover in the log
        log_file:flush()  -- Ensure the message is written immediately
    end
end)