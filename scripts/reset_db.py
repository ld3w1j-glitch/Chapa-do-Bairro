from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Banco resetado. Rode: python scripts/init_db.py")
