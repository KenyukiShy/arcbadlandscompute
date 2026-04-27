# Arc Badlands Fleet Liquidation Project Context

## Overview
This repository contains the web portal for the Arc Badlands fleet liquidation. The project features four primary assets managed through two regional colocation points: the South East Logistics Hub and the North Central Logistics Hub.

## Directory Architecture
- `/fleet_assets/[Asset_Name]/`: Contains optimized images (`01_XX.jpg`) and sidecar metadata (`01_XX.jpg.meta.json`).
- `gallery.js`: The central logic for fetching image metadata and rendering responsive gallery cards.
- `/combos/`: Strategic colocation listings for high-value infrastructure packages.
- `mkz.html`, `towncar.html`, `f350.html`, `jayco.html`: Individual high-fidelity asset listings.

## Asset Inventory & Verified Specs

### 1. 2016 Lincoln MKZ Hybrid
* **Hub**: North Central Logistics Hub (Hazen, ND)
* **Price Range**: $4,000 – $12,000
* **Mileage**: 100,000
* **Key Specs**: Retractable panoramic glass roof, Sync infotainment, 41/39 MPG
* **Disclosures**: Bonded title; requires HV Battery service

### 2. 1988 Lincoln Town Car Signature (Survivor)
* **Hub**: North Central Logistics Hub (Hazen, ND)
* **Price Range**: $8,000 – $16,000
* **Mileage**: 31,511 original miles
* **Key Specs**: 5.0L Windsor V8, digital instrument cluster, Ivory exterior, Tan leather
* **Provenance**: Original window sticker and maintenance logs (2009–2022) included

### 3. 2006 Ford F-350 King Ranch (SRW)
* **Hub**: South East Logistics Hub (Douglasville, GA)
* **Price Range**: $24,000 – $32,000
* **Mileage**: 47,000
* **Key Specs**: 6.8L Triton V10, 4x4, Saddle Brown King Ranch leather, Integrated 5th wheel prep

### 4. 2017 Jayco Eagle HT 26.5BHS
* **Hub**: North Central Logistics Hub (Hazen, ND)
* **Price Range**: $24,000 – $32,000
* **Tow Miles**: 2,400
* **Key Specs**: ClimateShield 4-season rating, LCI Ground Control 3.0 Auto-Leveling, Rear Bunkhouse slide

## Asset Packages & Combinations
* **HQ, Colocation, or Partner Package**: F-350 King Ranch + Jayco Eagle HT (Turnkey infrastructure for site management/adventure).
* **Regional Heritage Collection**: North Central Lincoln Pair (1988 Classic Survivor + 2016 Modern Hybrid).

## Technical Implementation Rules
* **Gallery Loader**: `loadFleetGallery(folder, count, prefix)` iterates using `padStart(2, '0')` to find files (e.g., `01_TC.jpg`).
* **Metadata**: Always fetch the `.meta.json` sidecar before rendering to populate titles and captions.
* **Responsive Design**: Ensure `photo-card` CSS supports varied screen sizes for mobile-first buyers.
