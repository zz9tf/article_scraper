import os
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).parent.parent.parent
dotenv_path = os.path.join(root, '.env')
load_dotenv(dotenv_path)