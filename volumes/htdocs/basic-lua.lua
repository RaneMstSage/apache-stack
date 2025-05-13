-- basic-lua.lua - Simple test script
function handle(r)
    r.content_type = "text/html"
    
    r:puts("<html><body>")
    r:puts("<h1>Lua is working!</h1>")
    r:puts("<p>Lua version: " .. _VERSION .. "</p>")
    r:puts("</body></html>")
    
    return apache2.OK
end