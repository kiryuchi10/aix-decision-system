# Jinja2 Report Templates

This folder contains Jinja2 templates for generating automated reports for Etch process data analysis.

## Templates

1. **base.html** - Base template with common layout, styles, and metadata
2. **spc_report.html** - SPC (Statistical Process Control) Summary Report
3. **fdc_report.html** - FDC (Fault Detection and Classification) Alarm Review Report
4. **rca_onepager.html** - RCA (Root Cause Analysis) 1-Pager

## Features

- **Graph Support**: Templates support embedding chart images (PNG/SVG)
- **Configurable Axes**: Data can be filtered/aggregated before rendering
- **User Customization**: Report metadata (title, author, time window) can be customized
- **Professional Styling**: Modern, clean design suitable for QC/QA documentation

## Usage

See `app/services/report_renderer.py` for rendering functions.

## API Endpoints

- `POST /api/v1/viz/reports/spc/generate` - Generate SPC report
- `POST /api/v1/viz/reports/fdc/generate` - Generate FDC report
- `POST /api/v1/viz/reports/rca/generate` - Generate RCA report

## Data Format

Each template expects specific data structures. See `report_renderer.py` docstrings for details.
