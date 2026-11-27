import urllib.request

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("pocasie")


@mcp.tool()
def pocasie(mesto: str) -> str:
    """Vráti aktuálne počasie v zadanom meste."""
    url = f"https://wttr.in/{mesto}?format=3"
    with urllib.request.urlopen(url) as odpoved:
        return odpoved.read().decode("utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")