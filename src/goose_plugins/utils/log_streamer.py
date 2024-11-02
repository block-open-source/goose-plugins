import asyncio
import aiofiles
import json
from pathlib import Path

LOG_FILE = Path.home() / ".goose" / "session_log.json"

async def stream_log():
    if not LOG_FILE.exists():
        print("No active Goose session log found.")
        return

    async with aiofiles.open(LOG_FILE, mode='r') as f:
        while True:
            line = await f.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            try:
                log_entry = json.loads(line)
                print(f"{log_entry['timestamp']} - {log_entry['action']}: {log_entry['details']}")
            except json.JSONDecodeError:
                print(f"Error decoding log entry: {line}")

def start_log_stream():
    asyncio.run(stream_log())