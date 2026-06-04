-- Pokemon HeartGold / SoulSilver memory dump helper for BizHawk.
--
-- Purpose:
-- 1. Load HGSS in BizHawk.
-- 2. Run this script once to list available memory domains.
-- 3. Set DUMP_DOMAIN below to one of the listed domains.
-- 4. Run before an event and after an event.
-- 5. Compare the two .bin files with MemoryResearch.py.
--
-- This does not connect to Archipelago yet.
-- This is only for memory research.

-- ============================================================
-- USER SETTINGS
-- ============================================================

-- Set this after the first run shows available domains.
-- Example possibilities might be "Main RAM", "ARM9 System Bus", etc.
-- The exact names depend on BizHawk/core, so do not guess.
local DUMP_DOMAIN = "nil"

-- Change this before each dump.
-- Examples:
-- "before_starter"
-- "after_starter"
-- "before_falkner"
-- "after_falkner"
local DUMP_LABEL = "hgss_dump"

-- Output folder.
-- This is relative to the folder BizHawk is running from unless you use
-- an absolute path.
--
-- Windows absolute path example:
-- local OUTPUT_DIRECTORY = "D:\\GitHub\\Archipelago\\hgss_archipelago\\memory_dumps"
local OUTPUT_DIRECTORY = "memory_dumps"

-- Start offset inside the chosen memory domain.
local DUMP_START = 0

-- nil means dump the whole selected domain.
-- For faster tests, set this to a smaller number such as 65536.
local DUMP_LENGTH = nil

-- Read/write chunks.
-- Keeping this moderate avoids trying to allocate one huge Lua string.
local CHUNK_SIZE = 4096

-- ============================================================
-- INTERNAL HELPERS
-- ============================================================

local function split_lines(value)
    local lines = {}

    for line in string.gmatch(value, "([^\r\n]+)") do
        table.insert(lines, line)
    end

    return lines
end

local function get_memory_domains()
    local domains = memory.getmemorydomainlist()

    if type(domains) == "string" then
        return split_lines(domains)
    end

    local domain_list = {}

    for _, domain in pairs(domains) do
        table.insert(domain_list, domain)
    end

    table.sort(domain_list)

    return domain_list
end

local function print_memory_domains()
    local domains = get_memory_domains()

    print("")
    print("Available BizHawk memory domains:")
    print("---------------------------------")

    for _, domain in ipairs(domains) do
        local ok, size = pcall(memory.getmemorydomainsize, domain)

        if ok then
            print(string.format("- %s (%d bytes)", domain, size))
        else
            print(string.format("- %s (size unavailable)", domain))
        end
    end

    print("---------------------------------")
    print("")
end

local function domain_exists(domain_name)
    local domains = get_memory_domains()

    for _, domain in ipairs(domains) do
        if domain == domain_name then
            return true
        end
    end

    return false
end

local function make_directory(directory)
    -- Windows-friendly. If the folder already exists, this may print a
    -- message in the Lua console, but it is harmless.
    os.execute('mkdir "' .. directory .. '"')
end

local function build_output_path()
    return OUTPUT_DIRECTORY .. "\\" .. DUMP_LABEL .. ".bin"
end

local function dump_memory_domain()
    if DUMP_DOMAIN == nil or DUMP_DOMAIN == "" then
        print("No DUMP_DOMAIN selected yet.")
        print("Set DUMP_DOMAIN near the top of this Lua file, then run again.")
        return
    end

    if not domain_exists(DUMP_DOMAIN) then
        print("Selected DUMP_DOMAIN does not exist: " .. DUMP_DOMAIN)
        print("Use one of the listed memory domains.")
        return
    end

    local domain_size = memory.getmemorydomainsize(DUMP_DOMAIN)
    local dump_length = DUMP_LENGTH or domain_size

    if DUMP_START < 0 then
        error("DUMP_START cannot be negative.")
    end

    if dump_length < 0 then
        error("DUMP_LENGTH cannot be negative.")
    end

    if DUMP_START + dump_length > domain_size then
        error(
            "Requested dump range is outside the selected memory domain. " ..
            "Start: " .. DUMP_START ..
            ", Length: " .. dump_length ..
            ", Domain size: " .. domain_size
        )
    end

    make_directory(OUTPUT_DIRECTORY)

    local output_path = build_output_path()
    local output_file = assert(io.open(output_path, "wb"))

    local remaining = dump_length
    local offset = DUMP_START

    memory.usememorydomain(DUMP_DOMAIN)

    while remaining > 0 do
        local chunk_size = math.min(CHUNK_SIZE, remaining)
        local bytes = {}

        for i = 0, chunk_size - 1 do
            local value = memory.readbyte(offset + i)
            bytes[#bytes + 1] = string.char(value)
        end

        output_file:write(table.concat(bytes))

        offset = offset + chunk_size
        remaining = remaining - chunk_size
    end

    output_file:close()

    print("")
    print("HGSS memory dump complete.")
    print("Domain: " .. DUMP_DOMAIN)
    print("Start: " .. DUMP_START)
    print("Length: " .. dump_length)
    print("Output: " .. output_path)
    print("")
end

-- ============================================================
-- RUN
-- ============================================================

print_memory_domains()
dump_memory_domain()