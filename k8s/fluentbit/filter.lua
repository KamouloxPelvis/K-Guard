-- filter.lua
-- This function processes incoming Falco logs to format them for Webex alerts
-- It extracts 'priority' and 'rule' fields to build a clean, human-readable message

function webex_formatter(tag, timestamp, record)
    -- Retrieve the 'priority' and 'rule' values from the record
    -- Fallback to 'unknown' if fields are missing to avoid nil errors
    local p = record["priority"] or "unknown"
    local r = record["rule"] or "unknown"
    
    -- Define the target Webex room ID for K-Guard alerts
    local room_id = "ROOM_ID"
    
    -- Construct the final record with only the fields required by the Webex API
    local new_record = {}
    new_record["roomId"] = room_id
    new_record["text"] = "Falco Alert detected: priority " .. p .. " on rule " .. r
    
    -- Return the reformatted record for the output plugin
    return 1, timestamp, new_record
end
