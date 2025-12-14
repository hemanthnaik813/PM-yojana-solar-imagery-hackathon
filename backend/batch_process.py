import pandas as pd
import json
from pathlib import Path
from inference import run_inference

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "input" / "samples.xlsx"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def process_excel():
    df = pd.read_excel(INPUT_FILE)
    results = []

    for _, row in df.iterrows():
        print(f"🔍 Processing sample_id={row['sample_id']}")
        result = run_inference(
            sample_id=row["sample_id"],
            lat=row["lat"],
            lon=row["lon"]
        )
        results.append(result)

    out_file = OUTPUT_DIR / "results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Processing complete. Results saved to {out_file}")
