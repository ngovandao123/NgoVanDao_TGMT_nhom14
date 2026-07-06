from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
CODE_DIR = PROJECT_DIR / 'code_start'

sys.path.insert(0, str(CODE_DIR))

from main import Game

if __name__ == '__main__':
	Game().run()