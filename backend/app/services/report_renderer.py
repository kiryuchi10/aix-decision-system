"""
Report Renderer Service
- Renders Jinja2 templates with data
- Generates HTML reports
- Supports PDF conversion (optional)
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "sop" / "jinja2"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "app" / "data" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)


def render_spc_report(
    spc_data: Dict[str, Any],
    report_meta: Dict[str, Any],
    data_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render SPC Summary Report
    
    Args:
        spc_data: {
            'mean': float,
            'std': float,
            'cpk': float,
            'cp': float,
            'ucl': float,
            'lcl': float,
            'violation_count': int,
            'charts': [
                {
                    'metric': str,
                    'chart_type': str,
                    'entity_type': str,
                    'entity_id': str,
                    'time_range': str,
                    'data_points': int,
                    'image_path': str (optional)
                }
            ],
            'violations': [
                {
                    'time': str,
                    'entity': str,
                    'metric': str,
                    'value': float,
                    'ucl': float,
                    'lcl': float,
                    'rule': str,
                    'severity': str
                }
            ],
            'cpk_trend_image': str (optional),
            'actions': [
                {
                    'priority': str,
                    'description': str
                }
            ]
        }
        report_meta: {
            'title': str,
            'process': str,
            'module': str,
            'time_window': str,
            'author': str,
            'version': str,
            'context': str (optional),
            'confidentiality': str (optional)
        }
        data_meta: {
            'row_count': int,
            'entity_count': int,
            'missing_rate': float
        } (optional)
    """
    template = env.get_template("spc_report.html")
    
    context = {
        "report": {
            **report_meta,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        },
        "spc": spc_data,
        "data": data_meta or {}
    }
    
    html_content = template.render(context)
    
    # Save to file
    filename = f"spc_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(filepath)


def render_fdc_report(
    fdc_data: Dict[str, Any],
    report_meta: Dict[str, Any],
    data_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render FDC Alarm Review Report
    
    Args:
        fdc_data: {
            'total': int,
            'active': int,
            'unique': int,
            'repeat_rate': float,
            'avg_yield_impact': float,
            'drift_rate': float,
            'pareto_image': str (optional),
            'type_distribution': Dict[str, int],
            'top_alarms': [
                {
                    'time': str,
                    'chamber': str,
                    'code': str,
                    'type': str,
                    'metric': str,
                    'value': float,
                    'threshold': float,
                    'sigma_distance': float,
                    'yield_impact': float,
                    'status': str
                }
            ],
            'heatmap_image': str (optional),
            'drift_summary': [
                {
                    'parameter': str,
                    'type': str,
                    'detected_at': str,
                    'current_value': float,
                    'expected_value': float,
                    'yield_impact': float
                }
            ],
            'recommendations': [
                {
                    'parameter': str,
                    'description': str,
                    'current_threshold': float (optional),
                    'suggested_threshold': float (optional)
                }
            ]
        }
    """
    template = env.get_template("fdc_report.html")
    
    context = {
        "report": {
            **report_meta,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        },
        "fdc": fdc_data,
        "data": data_meta or {}
    }
    
    html_content = template.render(context)
    
    filename = f"fdc_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(filepath)


def render_rca_report(
    rca_data: Dict[str, Any],
    report_meta: Dict[str, Any],
    data_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render RCA (Root Cause Analysis) 1-Pager
    
    Args:
        rca_data: {
            'what': str,
            'where': str,
            'when': str,
            'impact': str,
            'frequency': str (optional),
            'evidence': [
                {
                    'title': str,
                    'image': str (optional),
                    'summary': str,
                    'key_findings': List[str] (optional)
                }
            ],
            'hypotheses': [
                {
                    'description': str,
                    'evidence': str,
                    'confidence': int,
                    'status': str
                }
            ],
            'root_cause': str,
            'root_cause_confidence': int (optional),
            'capa': [
                {
                    'type': str,
                    'description': str,
                    'priority': str,
                    'owner': str (optional),
                    'due_date': str (optional),
                    'status': str (optional)
                }
            ],
            'verification': {
                'plan': str,
                'metrics': List[str] (optional),
                'follow_up_date': str (optional)
            } (optional)
        }
    """
    template = env.get_template("rca_onepager.html")
    
    context = {
        "report": {
            **report_meta,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        },
        "rca": rca_data,
        "data": data_meta or {}
    }
    
    html_content = template.render(context)
    
    filename = f"rca_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(filepath)


def convert_html_to_pdf(html_path: str, pdf_path: Optional[str] = None) -> str:
    """
    Convert HTML to PDF using pdfkit (requires wkhtmltopdf)
    
    Args:
        html_path: Path to HTML file
        pdf_path: Output PDF path (optional, auto-generated if None)
    
    Returns:
        Path to generated PDF
    """
    try:
        import pdfkit
    except ImportError:
        raise ImportError("pdfkit not installed. Run: pip install pdfkit")
    
    if pdf_path is None:
        pdf_path = html_path.replace(".html", ".pdf")
    
    # Configure pdfkit (adjust path if needed)
    config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
    
    pdfkit.from_file(html_path, pdf_path, configuration=config)
    
    return pdf_path
