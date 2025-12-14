from ultralytics import YOLO
from pathlib import Path

from satellite import fetch_satellite_image
from area_capacity import estimate_area_capacity
from qc import qc_decision

# -------------------------------------------------
# Load model
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "best.pt"

model = YOLO(str(MODEL_PATH))


def run_inference(sample_id, lat, lon):
    """
    Governance-ready inference:
    - 1200 sq.ft buffer first
    - 2400 sq.ft fallback
    - Segmentation OR boxes supported
    """

    sample_id = int(sample_id)
    lat = float(lat)
    lon = float(lon)

    # ================= BUFFER 1 =================
    image_path, metadata = fetch_satellite_image(
        lat, lon, sample_id, buffer_meters=10
    )

    if image_path is None:
        return _unverifiable(sample_id, lat, lon, metadata)

    results = model(
        image_path,
        imgsz=640,     # 🔥 match training size
        conf=0.25,     # 🔥 safe for rooftop panels
        iou=0.5
    )[0]

    has_masks = results.masks is not None and len(results.masks) > 0
    has_boxes = results.boxes is not None and len(results.boxes) > 0
    has_solar = has_masks or has_boxes

    panel_count, area_sqm, capacity_kw, audit_path = (
        estimate_area_capacity(results, image_path, sample_id)
    )

    buffer_used = 1200

    # ================= BUFFER 2 =================
    if panel_count == 0:
        image_path, metadata = fetch_satellite_image(
            lat, lon, sample_id, buffer_meters=20
        )

        if image_path is None:
            return _unverifiable(sample_id, lat, lon, metadata)

        results = model(
            image_path,
            imgsz=640,
            conf=0.25,
            iou=0.5
        )[0]

        has_masks = results.masks is not None and len(results.masks) > 0
        has_boxes = results.boxes is not None and len(results.boxes) > 0
        has_solar = has_masks or has_boxes

        panel_count, area_sqm, capacity_kw, audit_path = (
            estimate_area_capacity(results, image_path, sample_id)
        )

        buffer_used = 2400

    confidence = (
        float(results.boxes.conf.mean())
        if has_solar and results.boxes is not None
        else 0.0
    )

    qc_status, qc_notes = qc_decision(has_solar, confidence)

    return {
        "sample_id": sample_id,
        "lat": lat,
        "lon": lon,
        "has_solar": has_solar,
        "confidence": round(confidence, 3),
        "panel_count_est": panel_count,
        "pv_area_sqm_est": round(area_sqm, 2),
        "capacity_kw_est": round(capacity_kw, 2),
        "buffer_radius_sqft": buffer_used,
        "qc_status": qc_status,
        "qc_notes": qc_notes,
        "bbox_or_mask": "segmentation",
        "image_metadata": metadata,
        "audit_image": str(audit_path) if audit_path else None
    }


def _unverifiable(sample_id, lat, lon, metadata):
    return {
        "sample_id": sample_id,
        "lat": lat,
        "lon": lon,
        "has_solar": False,
        "confidence": 0.0,
        "panel_count_est": 0,
        "pv_area_sqm_est": 0.0,
        "capacity_kw_est": 0.0,
        "buffer_radius_sqft": None,
        "qc_status": "NOT_VERIFIABLE",
        "qc_notes": ["satellite imagery unavailable"],
        "bbox_or_mask": None,
        "image_metadata": metadata,
        "audit_image": None
    }
