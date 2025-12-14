# AI-Powered Rooftop Solar PV Verification System

## Overview
This project implements a governance-ready, auditable AI pipeline to verify the presence of rooftop solar PV systems using satellite imagery and computer vision.

The system answers the question:

> “Has a rooftop solar system actually been installed at this location?”

It is designed to support large-scale verification for schemes such as **PM Surya Ghar: Muft Bijli Yojana**, where physical inspections are costly and slow.

---

## Key Features
- Satellite image retrieval using **ESRI World Imagery**
- AI-based rooftop solar detection using **YOLOv8 (segmentation)**
- Adaptive verification buffer:
  - **1200 sq.ft (~10 m)**
  - **2400 sq.ft (~20 m)** fallback
- Panel count, area (m²), and capacity (kW) estimation
- Audit-ready visual overlays (bounding boxes / masks)
- Governance-friendly **QC classification**

---

## System Architecture
Excel (lat/lon)
↓
Satellite Fetch (ESRI)
↓
AI Inference (YOLOv8)
↓
Area & Capacity Estimation
↓
QC Decision
↓
JSON Output + Audit Images


---

## Input
An Excel file (`samples.xlsx`) with:
- `sample_id`
- `latitude`
- `longitude`

---

## Output
For each site, a JSON record is generated with:
- `has_solar`
- `confidence`
- `panel_count_est`
- `pv_area_sqm_est`
- `capacity_kw_est`
- `buffer_radius_sqft`
- `qc_status`
- `qc_notes`
- `image_metadata`
- `audit_image` (if applicable)

Audit overlay images are saved in:


---

## QC Status Logic
| Status | Meaning |
|------|--------|
| VERIFIABLE | Clear visual evidence of presence or absence |
| NOT_VERIFIABLE | Insufficient or unavailable satellite imagery |

### Why NOT_VERIFIABLE occurs
Satellite imagery is an external dependency. In some cases:
- ESRI imagery may be temporarily unavailable
- Network throttling or regional coverage gaps may occur

Instead of failing, the system **gracefully degrades** and marks the site as `NOT_VERIFIABLE`, ensuring:
- No false positives
- Transparent governance decisions
- Auditability

This behavior is **intentional and compliant** with the problem statement.

---

## Model Details
- Model: YOLOv8-Segmentation
- Training Data:
  - Alfred Weber Institute (Roboflow)
  - LSGI547 Project (Roboflow)
  - Piscinas y Tenistable (Roboflow)
- Average panel assumptions:
  - Area ≈ **1.7 m²**
  - Capacity ≈ **0.33 kW**

---

## How to Run
```bash
python backend/main.py

“We apply physical size and rooftop context filters after detection to remove false positives like vehicles, ensuring governance-grade reliability without retraining.”