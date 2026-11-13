import json
from pathlib import Path
from database import engine, Base, SessionLocal
from models import Promotion

RESULTS_DIR = Path(r"C:\Users\adnan\Desktop\Smartfolio\student3_research\results")

def load_data():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("Clearing old data...")
    db.query(Promotion).delete()
    
    promo_file = RESULTS_DIR / "model_promotions.json"
    if promo_file.exists():
        with open(promo_file, "r") as f:
            data = json.load(f)
            for item in data:
                promo = Promotion(
                    date=item.get("date", "Unknown"),
                    champion_version=item.get("champion_version", "N/A"),
                    challenger_version=item.get("challenger_version", "N/A"),
                    decision=item.get("decision", "UNKNOWN"),
                    reason=item.get("reason", "")
                )
                db.add(promo)
        db.commit()
        print(f"Loaded {len(data)} promotion records into SQLite database.")
    else:
        print("model_promotions.json not found.")
        
    db.close()

if __name__ == "__main__":
    load_data()
