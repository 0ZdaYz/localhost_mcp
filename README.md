# localhost_mcp

An MCP server that lets Claude access your localhost and local network URLs.

## Features

- **fetch_url** - Fetch any URL (localhost, LAN, or external)
- **fetch_localhost** - Shorthand: just specify port and path  
- **check_ports** - Scan common dev ports to see what's running

## Installation

### 1. Install dependencies

```bash
cd localhost-mcp
pip install -r requirements.txt
```

Or install directly:
```bash
pip install mcp httpx pydantic
```

### 2. Test the server

```bash
python server.py --help
```

## Configuration for Claude Desktop

Add this to your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "localhost": {
      "command": "python",
      "args": ["/full/path/to/localhost-mcp/server.py"]
    }
  }
}
```

Replace `/full/path/to/` with the actual path.

### Windows Example

```json
{
  "mcpServers": {
    "localhost": {
      "command": "python",
      "args": ["C:\\Users\\YourName\\localhost-mcp\\server.py"]
    }
  }
}
```

### With Virtual Environment

If using a venv:

```json
{
  "mcpServers": {
    "localhost": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\localhost-mcp\\server.py"]
    }
  }
}
```

## Usage Examples

Once configured, you can ask Claude:

- "Check what's running on my local ports"
- "Fetch http://localhost:3000/api/health"
- "Get the content from port 8080, path /check/about"
- "Make a POST request to localhost:3000/api/users with this JSON body..."

## Tools Reference

### fetch_url
Full URL fetching with all options:
- `url` (required): Full URL to fetch
- `method`: HTTP method (GET, POST, etc.)
- `headers`: Optional headers dict
- `body`: Optional request body
- `timeout`: Request timeout (1-120 seconds)

### fetch_localhost  
Shorthand for localhost:
- `port` (required): Port number
- `path`: URL path (default: "/")
- `method`, `headers`, `body`: Same as fetch_url

### check_ports
No parameters - scans common dev ports (3000, 5000, 8080, etc.)

## Security Note

This server can access any URL from your machine, including localhost and LAN addresses. Only use it in trusted environments.

## Troubleshooting

**"mcp module not found"**
```bash
pip install mcp
```

**Server won't start**
Check Python version (3.10+ recommended) and ensure all dependencies are installed.

**Connection refused**
Make sure your local server is actually running on the specified port.
