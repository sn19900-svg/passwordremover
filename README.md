# StructuralAI Pro 🏗️
### Intelligent Structural Design System

A Python terminal application for automatic structural design of buildings from basic parameters. Designed to run on **Termux (Android)** and any Linux/Mac terminal.

---

## Features

| Feature | Description |
|---|---|
| **Column Design** | Axial + biaxial bending, ACI 318-19 |
| **Beam Design** | Flexure + shear, stirrup design |
| **Slab Design** | Two-way, flat slab, ribbed slab systems |
| **Foundation Design** | Isolated footings (punching + flexure) |
| **Structural Analysis** | Portal method, gravity + lateral loads |
| **Quantity Takeoff** | Concrete, steel, formwork, earthwork |
| **Excel Reports** | Multi-sheet workbook with charts |
| **Drawing PDFs** | Foundation plan, framing plan, 3D wireframe |
| **Design Codes** | ACI 318-19, EC2, SBC 304 (Saudi) |

---

## Installation (Termux)

```bash
# 1. Copy files to Termux
# 2. Run installer:
bash install.sh

# 3. Start the app:
python3 main.py
```

## Installation (Linux / Mac)

```bash
pip install -r requirements.txt
python3 main.py
```

---

## Usage Flow

```
1. New Building Project
   → Enter floors, bays, materials, code

2. Structural Analysis
   → Gravity + lateral load analysis
   → Story shear diagrams

3. Design Elements
   → Auto-design all elements or individual ones
   → Columns, beams, slabs, footings

4. Quantity Takeoff
   → Concrete m³, Steel kg/ton, Formwork m²

5. Generate Reports
   → Excel (.xlsx) with 6 sheets + charts
   → PDF with 4 drawing pages (plans + 3D)
```

---

## Output Files

All outputs are saved to `./output/`:

- `ProjectName_YYYYMMDD_HHMMSS.xlsx` — Bill of Quantities
- `ProjectName_YYYYMMDD_HHMMSS_plans.pdf` — Structural Drawings

---

## Project Structure

```
structural_analyzer/
├── main.py                  ← Entry point
├── requirements.txt
├── install.sh               ← Termux installer
├── modules/
│   ├── codes.py             ← ACI/EC2/SBC constants
│   ├── geometry.py          ← Grid, column, beam generation
│   ├── design.py            ← Element design engine
│   ├── analysis.py          ← Structural analysis
│   ├── quantities.py        ← Quantity takeoff
│   ├── excel_report.py      ← Excel output
│   ├── drawings.py          ← PDF drawings
│   └── ui.py                ← Terminal UI
└── output/                  ← Generated files
```

---

## Supported Building Types

- Residential
- Office
- Commercial

## Design Codes

| Code | Country |
|---|---|
| ACI 318-19 | USA / International |
| EC2 | Europe |
| SBC 304 | Saudi Arabia |

---

## Technical Notes

- **Analysis method**: Portal Method for lateral loads, tributary area for gravity
- **Column design**: ACI 318-19 Section 22.4 (tied columns)
- **Beam design**: ACI 318-19 Sections 9.6, 22.5, 22.6
- **Slab design**: ACI Direct Design Method (two-way slabs)
- **Footing design**: ACI 318-19 Chapter 13 (punching + flexure)
- **Steel ratios**: Automatically clamped to ρmin–ρmax per code
- **Cover**: 40mm for beams/columns, 20mm for slabs, 75mm for footings

---

*Developed for structural engineers. Not a substitute for professional engineering judgment.*
