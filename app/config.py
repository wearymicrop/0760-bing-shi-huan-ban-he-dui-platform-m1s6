import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo('Asia/Shanghai')
VERSION = '冰时-2026.11.2'
SAMPLES = {'night': '周末夜场', 'clean': '例行早场'}
MAX_BYTES = 256 * 1024
MAX_ROWS = 1_200
DATABASE = os.environ.get('RINK_DB', str(ROOT / 'instance' / 'shifts.db'))
