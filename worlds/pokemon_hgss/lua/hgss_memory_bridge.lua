-- Pokemon HeartGold / SoulSilver live memory bridge for BizHawk.
--
-- This script watches a small set of researched Main RAM bytes and writes a
-- tiny JSON bridge state file that Python tools can read later.
--
-- This does not connect to Archipelago.
-- This does not send checks.
-- It only writes local state for development.

-- ============================================================
-- USER SETTINGS
-- ============================================================

local MEMORY_DOMAIN = "Main RAM"

-- Relative to the folder BizHawk is running from unless changed to an
-- absolute path for local testing.
local OUTPUT_DIRECTORY = "hgss_bridge_state"
local OUTPUT_FILENAME = "hgss_bridge_state.json"

-- Write bridge state every N frames.
local WRITE_EVERY_FRAMES = 120

-- ============================================================
-- WATCHED EVENTS
-- ============================================================

local WATCHED_EVENTS = {
    {
        event_key = "received_starter",
        notes = "Tentative Main RAM mapping for receiving any starter Pokemon.",
        requirements = {
            {
                address = 0x00110B40,
                bit_mask = 0x02,
                notes = "Primary received_starter candidate bit.",
            },
            {
                address = 0x00110B46,
                bit_mask = 0x04,
                notes = "Second required received_starter candidate bit.",
            },
        },
    },
}

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
    os.execute('mkdir "' .. directory .. '"')
end

local function build_output_path()
    return OUTPUT_DIRECTORY .. "\\" .. OUTPUT_FILENAME
end

local function bool_to_json(value)
    if value then
        return "true"
    end

    return "false"
end

local function json_escape(value)
    value = string.gsub(value, "\\", "\\\\")
    value = string.gsub(value, "\"", "\\\"")
    value = string.gsub(value, "\n", "\\n")
    value = string.gsub(value, "\r", "\\r")
    value = string.gsub(value, "\t", "\\t")

    return value
end

local function json_string(value)
    return "\"" .. json_escape(value) .. "\""
end

local function to_hex(value, width)
    return string.format("0x%0" .. width .. "X", value)
end

local function bit_is_set(byte_value, bit_mask)
    -- This is intentionally arithmetic instead of bit.band so it works in
    -- BizHawk Lua environments where the bit library may vary.
    --
    -- This expects single-bit masks such as 0x01, 0x02, 0x04, etc.
    return byte_value % (bit_mask * 2) >= bit_mask
end

local function get_frame_count()
    local ok, frame_count = pcall(emu.framecount)

    if ok then
        return frame_count
    end

    return 0
end

local function read_requirement(requirement)
    local byte_value = memory.readbyte(requirement.address)
    local is_set = bit_is_set(byte_value, requirement.bit_mask)

    return {
        address = requirement.address,
        address_hex = to_hex(requirement.address, 8),
        bit_mask = requirement.bit_mask,
        bit_mask_hex = to_hex(requirement.bit_mask, 2),
        byte_value = byte_value,
        byte_value_hex = to_hex(byte_value, 2),
        is_set = is_set,
        notes = requirement.notes,
    }
end

local function read_event_state(event_data)
    local requirements = {}
    local event_is_set = true

    for _, requirement in ipairs(event_data.requirements) do
        local requirement_state = read_requirement(requirement)
        table.insert(requirements, requirement_state)

        if not requirement_state.is_set then
            event_is_set = false
        end
    end

    return {
        event_key = event_data.event_key,
        is_set = event_is_set,
        notes = event_data.notes,
        requirements = requirements,
    }
end

local function read_all_event_states()
    local event_states = {}

    memory.usememorydomain(MEMORY_DOMAIN)

    for _, event_data in ipairs(WATCHED_EVENTS) do
        table.insert(event_states, read_event_state(event_data))
    end

    return event_states
end

local function write_requirement_json(output_file, requirement_state, is_last)
    output_file:write("        {\n")
    output_file:write("          \"address\": " .. requirement_state.address .. ",\n")
    output_file:write("          \"address_hex\": " .. json_string(requirement_state.address_hex) .. ",\n")
    output_file:write("          \"bit_mask\": " .. requirement_state.bit_mask .. ",\n")
    output_file:write("          \"bit_mask_hex\": " .. json_string(requirement_state.bit_mask_hex) .. ",\n")
    output_file:write("          \"byte_value\": " .. requirement_state.byte_value .. ",\n")
    output_file:write("          \"byte_value_hex\": " .. json_string(requirement_state.byte_value_hex) .. ",\n")
    output_file:write("          \"is_set\": " .. bool_to_json(requirement_state.is_set) .. ",\n")
    output_file:write("          \"notes\": " .. json_string(requirement_state.notes) .. "\n")

    if is_last then
        output_file:write("        }\n")
    else
        output_file:write("        },\n")
    end
end

local function write_event_state_json(output_file, event_state, is_last)
    output_file:write("    " .. json_string(event_state.event_key) .. ": {\n")
    output_file:write("      \"is_set\": " .. bool_to_json(event_state.is_set) .. ",\n")
    output_file:write("      \"notes\": " .. json_string(event_state.notes) .. ",\n")
    output_file:write("      \"requirements\": [\n")

    for requirement_index, requirement_state in ipairs(event_state.requirements) do
        write_requirement_json(
            output_file,
            requirement_state,
            requirement_index == #event_state.requirements
        )
    end

    output_file:write("      ]\n")

    if is_last then
        output_file:write("    }\n")
    else
        output_file:write("    },\n")
    end
end

local function write_bridge_state(event_states)
    make_directory(OUTPUT_DIRECTORY)

    local output_path = build_output_path()
    local temp_output_path = output_path .. ".tmp"
    local output_file = assert(io.open(temp_output_path, "w"))

    output_file:write("{\n")
    output_file:write("  \"format_version\": 1,\n")
    output_file:write("  \"game\": \"Pokemon HeartGold/SoulSilver\",\n")
    output_file:write("  \"memory_domain\": " .. json_string(MEMORY_DOMAIN) .. ",\n")
    output_file:write("  \"frame_count\": " .. get_frame_count() .. ",\n")
    output_file:write("  \"event_states\": {\n")

    for event_index, event_state in ipairs(event_states) do
        write_event_state_json(
            output_file,
            event_state,
            event_index == #event_states
        )
    end

    output_file:write("  }\n")
    output_file:write("}\n")
    output_file:close()

    os.remove(output_path)
    os.rename(temp_output_path, output_path)

    return output_path
end

local function print_event_changes(event_states, previous_event_states)
    for _, event_state in ipairs(event_states) do
        local previous_value = previous_event_states[event_state.event_key]

        if previous_value == nil or previous_value ~= event_state.is_set then
            print(
                "HGSS bridge event state changed: " ..
                event_state.event_key ..
                " = " ..
                tostring(event_state.is_set)
            )

            previous_event_states[event_state.event_key] = event_state.is_set
        end
    end
end

local function validate_setup()
    if not domain_exists(MEMORY_DOMAIN) then
        print("Selected MEMORY_DOMAIN does not exist: " .. MEMORY_DOMAIN)
        print("Available domains:")

        for _, domain in ipairs(get_memory_domains()) do
            print("- " .. domain)
        end

        return false
    end

    return true
end

-- ============================================================
-- RUN
-- ============================================================

if not validate_setup() then
    return
end

print("")
print("Pokemon HGSS memory bridge started.")
print("Domain: " .. MEMORY_DOMAIN)
print("Output: " .. build_output_path())
print("Write interval: every " .. WRITE_EVERY_FRAMES .. " frames")
print("")

local previous_event_states = {}
local last_write_frame = -WRITE_EVERY_FRAMES

while true do
    local current_frame = get_frame_count()

    if current_frame - last_write_frame >= WRITE_EVERY_FRAMES then
        local event_states = read_all_event_states()
        local output_path = write_bridge_state(event_states)

        print_event_changes(event_states, previous_event_states)

        last_write_frame = current_frame
    end

    emu.frameadvance()
end