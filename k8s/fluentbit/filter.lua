function webex_formatter(tag, timestamp, record)
    -- 1. Read token from the file 
    local f = io.open("/var/run/secrets/token/token.txt", "r")
    local token = ""
    if f then
        token = f:read("*a"):gsub("%s+", "")
        f:close()
    else
        token = "ERROR_TOKEN_MISSING"
    end

    -- 2. Extract information from the alert 
    local p = record["priority"] or "unknown"
    local r = record["rule"] or "unknown"
    local room_id = "Y2lzY29zcGFyazovL3VybjpURUFNOmV1LWNlbnRyYWwtMV9rL1JPT00vYWE2MjM5MDAtMTczNy0xMWYxLTg4ZDItY2IyY2E0NThhOTU4"

    -- 3. Create formated record for Webex
    -- Fluent Bit would send the JSON to the Webex endpoint 
    local new_record = {}
    new_record["roomId"] = room_id
    new_record["text"] = "Falco Alert [" .. p .. "]: " .. r
    
    -- We add the token in  metadata that Fluent Bit will use or we
    --  manage it directly in here if use lua HTTP library 
    new_record["auth_token"] = token

    return 1, timestamp, new_record
end
