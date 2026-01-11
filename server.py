#!/usr/bin/env python3
"""
localhost_mcp - MCP server for fetching localhost and local network URLs.

This server allows Claude to access your local development servers,
APIs running on localhost, and other local network resources.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import httpx

# Initialize the MCP server
mcp = FastMCP("localhost_mcp")

# Configuration
DEFAULT_TIMEOUT = 30.0
MAX_CONTENT_LENGTH = 500_000  # 500KB max response


class FetchUrlInput(BaseModel):
    """Input model for fetching any URL."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    url: str = Field(
        ..., 
        description="Full URL to fetch (e.g., 'http://localhost:3000/api/users')",
        min_length=1
    )
    method: str = Field(
        default="GET",
        description="HTTP method: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS"
    )
    headers: Optional[dict] = Field(
        default=None,
        description="Optional HTTP headers as key-value pairs"
    )
    body: Optional[str] = Field(
        default=None,
        description="Optional request body for POST/PUT/PATCH requests"
    )
    timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        description="Request timeout in seconds",
        ge=1,
        le=120
    )


class FetchLocalhostInput(BaseModel):
    """Input model for localhost shorthand."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    port: int = Field(
        ...,
        description="Port number (e.g., 3000, 8080, 5173)",
        ge=1,
        le=65535
    )
    path: str = Field(
        default="/",
        description="URL path (e.g., '/api/users', '/check/about#api-documentation')"
    )
    method: str = Field(
        default="GET",
        description="HTTP method"
    )
    headers: Optional[dict] = Field(
        default=None,
        description="Optional HTTP headers"
    )
    body: Optional[str] = Field(
        default=None,
        description="Optional request body"
    )


async def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    body: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT
) -> str:
    """Make HTTP request and return formatted response."""
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            # Prepare request kwargs
            kwargs = {"headers": headers or {}}
            if body and method.upper() in ("POST", "PUT", "PATCH"):
                kwargs["content"] = body
            
            # Make the request
            response = await client.request(method.upper(), url, **kwargs)
            
            # Get response info
            status = response.status_code
            content_type = response.headers.get("content-type", "unknown")
            
            # Get response body
            content = response.text
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + f"\n\n... [TRUNCATED - Response exceeded {MAX_CONTENT_LENGTH} bytes]"
            
            # Format response
            result = f"""## Response from {url}

**Status:** {status} {response.reason_phrase}
**Content-Type:** {content_type}
**Content-Length:** {len(response.content)} bytes

### Headers
"""
            for key, value in response.headers.items():
                result += f"- {key}: {value}\n"
            
            result += f"\n### Body\n\n```\n{content}\n```"
            
            return result
            
        except httpx.ConnectError as e:
            return f"**Connection Error:** Could not connect to {url}\n\nMake sure the server is running. Error: {e}"
        except httpx.TimeoutException:
            return f"**Timeout:** Request to {url} timed out after {timeout} seconds"
        except httpx.HTTPStatusError as e:
            return f"**HTTP Error:** {e.response.status_code} - {e.response.reason_phrase}"
        except Exception as e:
            return f"**Error:** {type(e).__name__}: {e}"


@mcp.tool(
    name="fetch_url",
    annotations={
        "title": "Fetch URL",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fetch_url(params: FetchUrlInput) -> str:
    """Fetch any URL including localhost, local network, and external URLs.
    
    Use this tool to access local development servers, APIs, and web pages.
    Supports all HTTP methods and custom headers.
    
    Examples:
    - http://localhost:3000/
    - http://127.0.0.1:8080/api/health
    - http://192.168.1.100:5000/data
    
    Args:
        params: FetchUrlInput containing url, method, headers, body, timeout
    
    Returns:
        Formatted response with status, headers, and body content
    """
    return await make_request(
        url=params.url,
        method=params.method,
        headers=params.headers,
        body=params.body,
        timeout=params.timeout
    )


@mcp.tool(
    name="fetch_localhost",
    annotations={
        "title": "Fetch Localhost",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fetch_localhost(params: FetchLocalhostInput) -> str:
    """Shorthand for fetching localhost URLs - just specify port and path.
    
    Convenient for quickly accessing local dev servers without typing full URL.
    
    Examples:
    - port=3000, path="/" -> http://localhost:3000/
    - port=8080, path="/api/users" -> http://localhost:8080/api/users
    
    Args:
        params: FetchLocalhostInput containing port, path, method, headers, body
    
    Returns:
        Formatted response with status, headers, and body content
    """
    # Build localhost URL
    path = params.path if params.path.startswith("/") else f"/{params.path}"
    url = f"http://localhost:{params.port}{path}"
    
    return await make_request(
        url=url,
        method=params.method,
        headers=params.headers,
        body=params.body
    )


@mcp.tool(
    name="check_ports",
    annotations={
        "title": "Check Common Ports",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def check_ports() -> str:
    """Scan common development ports to see what's running locally.
    
    Checks ports commonly used by dev servers:
    - 3000 (React, Next.js, Express)
    - 3001 (secondary React)
    - 4000 (various)
    - 5000 (Flask, Python)
    - 5173 (Vite)
    - 5174 (Vite secondary)
    - 8000 (Django, FastAPI)
    - 8080 (Java, various)
    - 8888 (Jupyter)
    
    Returns:
        List of ports with their status (open/closed)
    """
    common_ports = [3000, 3001, 4000, 5000, 5173, 5174, 8000, 8080, 8888]
    results = ["## Local Port Scan Results\n"]
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for port in common_ports:
            url = f"http://localhost:{port}/"
            try:
                response = await client.get(url)
                status = f"✅ **OPEN** - Status {response.status_code}"
            except httpx.ConnectError:
                status = "❌ Closed/Not responding"
            except httpx.TimeoutException:
                status = "⏳ Timeout (might be busy)"
            except Exception as e:
                status = f"⚠️ Error: {type(e).__name__}"
            
            results.append(f"- **Port {port}:** {status}")
    
    return "\n".join(results)


if __name__ == "__main__":
    # Run with stdio transport (default for local MCP servers)
    mcp.run()
