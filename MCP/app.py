from fastmcp import FastMCP
from datetime import datetime
import pytz

mcp = FastMCP("DateTime MCP")


@mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in a specified timezone.

    Args:
        timezone: Timezone name (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York'). Defaults to UTC.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%H:%M:%S %Z (UTC%z)")
    except pytz.UnknownTimeZoneError:
        return f"Unknown timezone: '{timezone}'. Use a valid tz name like 'Asia/Kolkata' or 'America/New_York'."


@mcp.tool()
def get_current_date(timezone: str = "UTC") -> str:
    """Get the current date in a specified timezone.

    Args:
        timezone: Timezone name (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York'). Defaults to UTC.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%A, %B %d, %Y")
    except pytz.UnknownTimeZoneError:
        return f"Unknown timezone: '{timezone}'. Use a valid tz name like 'Asia/Kolkata' or 'America/New_York'."


@mcp.tool()
def get_current_datetime(timezone: str = "UTC") -> str:
    """Get the current date and time together in a specified timezone.

    Args:
        timezone: Timezone name (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York'). Defaults to UTC.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%A, %B %d, %Y — %H:%M:%S %Z (UTC%z)")
    except pytz.UnknownTimeZoneError:
        return f"Unknown timezone: '{timezone}'. Use a valid tz name like 'Asia/Kolkata' or 'America/New_York'."


@mcp.tool()
def list_timezones(region: str = "") -> str:
    """List available timezones, optionally filtered by region.

    Args:
        region: Filter timezones by region prefix (e.g. 'Asia', 'America', 'Europe'). Leave empty for all.
    """
    all_tz = pytz.all_timezones
    if region:
        filtered = [tz for tz in all_tz if tz.startswith(region)]
        if not filtered:
            return f"No timezones found for region '{region}'."
        return "\n".join(filtered)
    return "\n".join(all_tz)


if __name__ == "__main__":
    mcp.run(transport="stdio")
