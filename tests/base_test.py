from pathlib import Path
CURRENT_FILE = Path(__file__).absolute()
TEST_DIR = CURRENT_FILE.parent
ROOT_DIR = TEST_DIR.parent
PROTOCOL_DIR = ROOT_DIR / "protocol"