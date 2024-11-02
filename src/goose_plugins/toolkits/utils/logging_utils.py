import logging
import sys
from pathlib import Path

def setup_logging():
    """Set up logging for the CriticalSystemsThinking toolkit."""
    log_file = Path.home() / ".goose" / "critical_systems_thinking.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def log_action(log_file, action: str, details: str):
    """Log an action to the session log file."""
    import time
    import json
    
    log_entry = {
        "timestamp": time.time(),
        "action": action,
        "details": details
    }
    with open(log_file, 'a') as f:
        json.dump(log_entry, f)
        f.write('\n')