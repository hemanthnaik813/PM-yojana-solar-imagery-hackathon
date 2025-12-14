import requests
import time
from pathlib import Path

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "sat_images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Demo fallback image (YOU MUST ADD THIS FILE)
DEMO_IMAGE = BASE_DIR / "sample_data" / "demo_rooftop_solar.jpg"

# -------------------------------------------------
# ESRI Config
# -------------------------------------------------
ESRI_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/export"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (AI Rooftop PV Verification)"
}

# -------------------------------------------------
# Internal helper
# -------------------------------------------------
def _try_fetch(lat, lon, buffer_meters, sample_id):
    """
    Try fetching satellite image with given buffer.
    Returns (image_path, bbox) or (None, bbox)
    """
    delta = buffer_meters / 111000  # meters → degrees
    bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"

    params = {
        "bbox": bbox,
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": "640,640",
        "format": "png",
        "f": "image"
    }

    try:
        response = requests.get(
            ESRI_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )
    except Exception:
        return None, bbox

    if response.status_code == 200 and len(response.content) > 5000:
        out_img = OUTPUT_DIR / f"site_{sample_id}.png"
        with open(out_img, "wb") as f:
            f.write(response.content)
        return out_img, bbox

    return None, bbox


# -------------------------------------------------
# Public API
# -------------------------------------------------
def fetch_satellite_image(lat, lon, sample_id, buffer_meters=10):
    """
    Satellite fetch logic:
    1) Try live ESRI imagery
    2) Retry with larger buffer
    3) Fallback to demo satellite image (guaranteed)
    """

    lat = float(lat)
    lon = float(lon)
    sample_id = int(sample_id)

    # ---------------- Attempt 1 ----------------
    img, bbox = _try_fetch(lat, lon, buffer_meters, sample_id)
    if img:
        return img, {
            "source": "ESRI World Imagery",
            "buffer_meters": buffer_meters,
            "bbox": bbox,
            "note": "primary fetch"
        }

    # ---------------- Attempt 2 ----------------
    time.sleep(1)
    fallback_buffer = max(buffer_meters * 2, 30)
    img, bbox = _try_fetch(lat, lon, fallback_buffer, sample_id)
    if img:
        return img, {
            "source": "ESRI World Imagery",
            "buffer_meters": fallback_buffer,
            "bbox": bbox,
            "note": "fallback fetch (expanded buffer)"
        }

    # ---------------- FINAL DEMO FALLBACK ----------------
    if DEMO_IMAGE.exists():
        return DEMO_IMAGE, {
            "source": "Demo Satellite Image (Evaluation Mode)",
            "buffer_meters": buffer_meters,
            "bbox": "demo",
            "note": "live imagery unavailable; demo image used"
        }

    # Absolute last resort (should never happen)
    return None, {
        "source": "Unknown",
        "buffer_meters": None,
        "bbox": None,
        "note": "no imagery available"
    }
