import cv2
import numpy as np
from pathlib import Path

# -------------------------------------------------
# Domain assumptions (documented for audit)
# -------------------------------------------------
PANEL_AREA_SQM = 1.7        # average rooftop PV panel area
PANEL_CAPACITY_KW = 0.33   # ~330W per panel

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIT_DIR = BASE_DIR / "output" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def estimate_area_capacity(results, image_path, sample_id):
    """
    - Accepts YOLOv8 segmentation OR box outputs
    - Filters physically impossible detections (cars/roads)
    - Saves audit overlay image
    """

    image = cv2.imread(str(image_path))
    if image is None:
        return 0, 0.0, 0.0, None

    overlay = image.copy()
    h, w = image.shape[:2]
    image_area = h * w

    panel_count = 0

    # =================================================
    # CASE 1: SEGMENTATION MASKS
    # =================================================
    if results.masks is not None:
        masks = results.masks.data.cpu().numpy()

        for mask in masks:
            mask_bin = (mask > 0.4).astype(np.uint8)
            mask_area = mask_bin.sum()
            area_ratio = mask_area / image_area

            # Physical sanity check (critical)
            if 0.0001 < area_ratio < 0.05:
                panel_count += 1

                contours, _ = cv2.findContours(
                    (mask_bin * 255).astype(np.uint8),
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)

    # =================================================
    # CASE 2: FALLBACK TO BOUNDING BOXES
    # =================================================
    elif results.boxes is not None and len(results.boxes) > 0:
        boxes = results.boxes.xyxy.cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            box_area = (x2 - x1) * (y2 - y1)
            area_ratio = box_area / image_area

            if 0.0001 < area_ratio < 0.05:
                panel_count += 1
                cv2.rectangle(
                    overlay,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

    # =================================================
    # ESTIMATION
    # =================================================
    area_sqm = panel_count * PANEL_AREA_SQM
    capacity_kw = panel_count * PANEL_CAPACITY_KW

    audit_path = AUDIT_DIR / f"site_{sample_id}_audit.png"
    cv2.imwrite(str(audit_path), overlay)

    return panel_count, area_sqm, capacity_kw, audit_path
