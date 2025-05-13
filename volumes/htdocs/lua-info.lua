function handle(r)
    r.content_type = "text/html; charset=utf-8"
    
    -- Enhanced HTML structure with PHP-like styling
    r:puts([[
<!DOCTYPE html>
<html>
<head>
    <title>Lua Info</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; color: #222; background: #fff; }
        h1 { background-color: #8892BF; color: white; padding: 10px 15px; margin: 0; }
        h2 { background-color: #E2E4EF; color: #333; padding: 5px 15px; margin: 0; border-top: 1px solid #ccc; }
        table { border-collapse: collapse; width: 100%; margin: 0; }
        td, th { border: 1px solid #ccc; padding: 6px; }
        .e { width: 30%; background-color: #f2f2f2; font-weight: bold; }
        .v { background-color: #fff; }
        tr:nth-child(even) .v { background-color: #f8f8f8; }
        .center { text-align: center; }
        .section { margin-bottom: 20px; }
        .footer { font-size: 0.8em; text-align: right; padding: 5px 15px; color: #777; }
    </style>
</head>
<body>
    <h1>Lua Info</h1>
]])
    
    -- Lua Version
    r:puts("<h2>Lua Environment</h2>")
    r:puts("<table>")
    r:puts("<tr><td class='e'>Lua Version</td><td class='v'>" .. _VERSION .. "</td></tr>")
    r:puts("<tr><td class='e'>Apache Version</td><td class='v'>" .. apache2.version .. "</td></tr>")
    r:puts("<tr><td class='e'>Lua Handler</td><td class='v'>mod_lua</td></tr>")
    r:puts("</table>")
    
    -- Request Information - These are known to work
    r:puts("<h2>Request Information</h2>")
    r:puts("<table>")
    r:puts("<tr><td class='e'>Method</td><td class='v'>" .. tostring(r.method) .. "</td></tr>")
    r:puts("<tr><td class='e'>URI</td><td class='v'>" .. tostring(r.unparsed_uri) .. "</td></tr>")
    r:puts("<tr><td class='e'>Protocol</td><td class='v'>" .. tostring(r.protocol) .. "</td></tr>")
    r:puts("<tr><td class='e'>Hostname</td><td class='v'>" .. tostring(r.hostname) .. "</td></tr>")
    r:puts("<tr><td class='e'>Filename</td><td class='v'>" .. tostring(r.filename) .. "</td></tr>")
    r:puts("</table>")
    
    -- Common Request Headers - manually listed to avoid iteration issues
    r:puts("<h2>Common Request Headers</h2>")
    r:puts("<table>")
    
    -- List of common headers to check for
    local common_headers = {
        "Host", "User-Agent", "Accept", "Accept-Language", "Accept-Encoding",
        "Connection", "Referer", "Content-Type", "Content-Length"
    }
    
    -- Check for each common header
    for _, name in ipairs(common_headers) do
        -- Individual access should work even if iteration doesn't
        local value = r.headers_in[name]
        if value then
            r:puts("<tr><td class='e'>" .. name .. "</td><td class='v'>" .. tostring(value) .. "</td></tr>")
        end
    end
    r:puts("</table>")
    
    -- Lua Modules
    r:puts("<h2>Lua Modules</h2>")
    r:puts("<table>")
    local modules = {"os", "io", "string", "math", "table", "debug", "coroutine", "package"}
    for _, module_name in ipairs(modules) do
        local status = package.loaded[module_name] and "Loaded" or "Not loaded"
        r:puts("<tr><td class='e'>" .. module_name .. "</td><td class='v'>" .. status .. "</td></tr>")
    end
    r:puts("</table>")
    
    -- System Information if available
    if os and os.date then
        r:puts("<h2>System Information</h2>")
        r:puts("<table>")
        r:puts("<tr><td class='e'>Server Time</td><td class='v'>" .. os.date() .. "</td></tr>")
        r:puts("</table>")
    end
    
    -- Footer
    r:puts("<div class='footer'>Lua " .. _VERSION .. " | Apache " .. apache2.version .. "</div>")
    r:puts("</body></html>")
    
    return apache2.OK
end