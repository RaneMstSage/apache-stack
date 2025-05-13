def application(environ, start_response):
    """
    A simple WSGI application that displays Python environment information,
    similar to phpinfo() for PHP and the Lua info script.
    """
    import os
    import sys
    import platform
    import datetime
    
    status = '200 OK'  # This format is correct, but let's ensure nothing else modifies it
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Python Info</title>
    <style>
        body {{
            background-color: #fff;
            color: #222;
            font-family: sans-serif;
            padding: 0;
            margin: 0;
        }}
        h1 {{
            background-color: #4B8BBE;
            color: white;
            padding: 10px 15px;
            margin: 0;
        }}
        h2 {{
            background-color: #D6E9FF;
            color: #333;
            padding: 5px 15px;
            margin: 0;
            border-top: 1px solid #ccc;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 0;
        }}
        td, th {{
            border: 1px solid #ccc;
            padding: 6px;
        }}
        .e {{
            width: 30%;
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        .v {{
            background-color: #fff;
        }}
        tr:nth-child(even) .v {{
            background-color: #f8f8f8;
        }}
        .footer {{
            font-size: 0.8em;
            text-align: right;
            padding: 5px 15px;
            color: #777;
        }}
    </style>
</head>
<body>
    <h1>Python Info</h1>
    
    <h2>Python System Information</h2>
    <table>
        <tr><td class="e">Python Version</td><td class="v">{python_version}</td></tr>
        <tr><td class="e">Platform</td><td class="v">{platform}</td></tr>
        <tr><td class="e">System</td><td class="v">{system}</td></tr>
        <tr><td class="e">Architecture</td><td class="v">{architecture}</td></tr>
        <tr><td class="e">Executable</td><td class="v">{executable}</td></tr>
        <tr><td class="e">Date/Time</td><td class="v">{datetime}</td></tr>
        <tr><td class="e">WSGI Version</td><td class="v">{wsgi_version}</td></tr>
    </table>
    
    <h2>Request Information</h2>
    <table>
        <tr><td class="e">Request Method</td><td class="v">{request_method}</td></tr>
        <tr><td class="e">Request URI</td><td class="v">{request_uri}</td></tr>
        <tr><td class="e">Server Name</td><td class="v">{server_name}</td></tr>
        <tr><td class="e">Server Port</td><td class="v">{server_port}</td></tr>
        <tr><td class="e">Server Protocol</td><td class="v">{server_protocol}</td></tr>
        <tr><td class="e">Server Software</td><td class="v">{server_software}</td></tr>
        <tr><td class="e">Remote Address</td><td class="v">{remote_addr}</td></tr>
    </table>
    
    <h2>Request Headers</h2>
    <table>
        {request_headers}
    </table>
    
    <h2>Python Path</h2>
    <table>
        {python_path}
    </table>
    
    <h2>Python Modules</h2>
    <table>
        {python_modules}
    </table>
    
    <h2>Environment Variables</h2>
    <table>
        {environment_vars}
    </table>
    
    <div class="footer">Python {python_version} | WSGI {wsgi_version}</div>
</body>
</html>
"""
    
    # Gather system info
    py_version = sys.version.replace('\n', '')
    py_platform = platform.platform()
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Gather request info
    req_method = environ.get('REQUEST_METHOD', '')
    req_uri = environ.get('REQUEST_URI', environ.get('PATH_INFO', ''))
    server_name = environ.get('SERVER_NAME', '')
    server_port = environ.get('SERVER_PORT', '')
    server_protocol = environ.get('SERVER_PROTOCOL', '')
    server_software = environ.get('SERVER_SOFTWARE', '')
    remote_addr = environ.get('REMOTE_ADDR', '')
    
    # Format request headers
    request_headers = ""
    for key in sorted(environ):
        if key.startswith('HTTP_'):
            header_name = key[5:].replace('_', '-').title()
            request_headers += f'<tr><td class="e">{header_name}</td><td class="v">{environ[key]}</td></tr>\n'
    
    # Format Python path
    python_path = ""
    for i, path in enumerate(sys.path):
        python_path += f'<tr><td class="e">Path {i+1}</td><td class="v">{path}</td></tr>\n'
    
    # Format Python modules (only show a subset of common modules)
    python_modules = ""
    common_modules = ['os', 'sys', 'datetime', 'json', 'math', 'random', 're', 'time', 'platform']
    for module in common_modules:
        status_value = "Imported" if module in sys.modules else "Available"
        python_modules += f'<tr><td class="e">{module}</td><td class="v">{status_value}</td></tr>\n'
    
    # Format environment variables
    environment_vars = ""
    for key in sorted(environ.keys()):
        if not key.startswith('HTTP_') and not key.startswith('wsgi.'):
            environment_vars += f'<tr><td class="e">{key}</td><td class="v">{environ[key]}</td></tr>\n'
    
    # Format HTML response
    html = html.format(
        python_version=py_version,
        platform=py_platform,
        system=platform.system(),
        architecture=platform.architecture()[0],
        executable=sys.executable,
        datetime=current_datetime,
        wsgi_version=str(environ.get('wsgi.version', '')),
        request_method=req_method,
        request_uri=req_uri,
        server_name=server_name,
        server_port=server_port,
        server_protocol=server_protocol,
        server_software=server_software,
        remote_addr=remote_addr,
        request_headers=request_headers,
        python_path=python_path,
        python_modules=python_modules,
        environment_vars=environment_vars
    )
    
    # Make sure status is properly formatted
    response_headers = [('Content-type', 'text/html'),
                       ('Content-Length', str(len(html.encode('utf-8'))))]
    
    start_response(status, response_headers)
    
    return [html.encode('utf-8')]