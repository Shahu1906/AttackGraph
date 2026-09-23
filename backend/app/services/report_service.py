"""
AttackGraphX — Report generation service.

Generates real PDF and CSV reports from analysis pipeline data.
Uses ReportLab for PDF generation.
"""
import csv
import io
from datetime import datetime, timezone
from typing import Any

import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

log = structlog.get_logger(__name__)

# -----------------------------------------------------------------------
# Colour palette (matching AttackGraphX brand)
# -----------------------------------------------------------------------
_BRAND_BLUE = colors.HexColor("#2563eb")
_BRAND_DARK = colors.HexColor("#0f172a")
_SURFACE = colors.HexColor("#f8fafc")
_BORDER = colors.HexColor("#e2e8f0")
_CRITICAL = colors.HexColor("#ef4444")
_HIGH = colors.HexColor("#f97316")
_MEDIUM = colors.HexColor("#eab308")
_LOW = colors.HexColor("#22c55e")
_WHITE = colors.white

_SEV_COLOR = {
    "critical": _CRITICAL,
    "high": _HIGH,
    "medium": _MEDIUM,
    "low": _LOW,
}


def _sev_color(sev: str) -> Any:
    return _SEV_COLOR.get((sev or "low").lower(), _LOW)


# -----------------------------------------------------------------------
# PDF generation
# -----------------------------------------------------------------------

def generate_pdf(paths: list, patches: list, target: str = "all") -> bytes:
    """
    Generate a professional AttackGraphX security assessment PDF.
    Returns raw bytes ready for StreamingResponse.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="AttackGraphX Security Assessment",
        author="AttackGraphX Platform",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "AGXTitle",
        parent=styles["Title"],
        textColor=_BRAND_DARK,
        fontSize=22,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "AGXSubtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#64748b"),
        fontSize=11,
        spaceAfter=2,
    )
    heading1_style = ParagraphStyle(
        "AGXHeading1",
        parent=styles["Heading1"],
        textColor=_BRAND_BLUE,
        fontSize=14,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    heading2_style = ParagraphStyle(
        "AGXHeading2",
        parent=styles["Heading2"],
        textColor=_BRAND_DARK,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "AGXBody",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=4,
        leading=14,
    )
    mono_style = ParagraphStyle(
        "AGXMono",
        parent=styles["Code"],
        fontSize=8,
        spaceAfter=2,
        fontName="Courier",
        textColor=colors.HexColor("#1e293b"),
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    target_label = f"Target: {target.upper()}"

    # Computed stats
    total_paths = len(paths)
    critical_paths = sum(1 for p in paths if (p.get("severity") or "").lower() == "critical")
    high_paths = sum(1 for p in paths if (p.get("severity") or "").lower() == "high")
    avg_risk = (
        round(sum(p.get("risk_score", 0) for p in paths) / total_paths)
        if total_paths
        else 0
    )
    hosts_set = set()
    cve_set = set()
    for p in paths:
        for h in p.get("hops", []):
            if h.get("host"):
                hosts_set.add(h["host"])
            if h.get("vulnerability"):
                cve_set.add(h["vulnerability"])

    story = []

    # ---- Title Page ----
    story.append(Paragraph("AttackGraph<font color='#2563eb'>X</font>", title_style))
    story.append(Paragraph("Enterprise Security Assessment Report", subtitle_style))
    story.append(Paragraph(f"Generated: {now}  |  {target_label}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=_BRAND_BLUE, spaceAfter=12))

    # ---- Executive Summary ----
    story.append(Paragraph("Executive Summary", heading1_style))
    story.append(Paragraph(
        f"This report summarises the attack-path analysis performed by the AttackGraphX platform. "
        f"A total of <b>{total_paths}</b> exploitable attack paths were identified across the target infrastructure. "
        f"Of these, <b>{critical_paths}</b> are rated <b>CRITICAL</b> and <b>{high_paths}</b> are rated <b>HIGH</b>, "
        f"requiring immediate remediation attention. The average composite risk score across all identified paths "
        f"is <b>{avg_risk}/100</b>. <b>{len(hosts_set)}</b> unique hosts are involved in one or more attack chains. "
        f"<b>{len(cve_set)}</b> distinct CVEs have been identified as exploitation vectors.",
        body_style,
    ))

    # ---- Risk Summary Table ----
    story.append(Paragraph("Risk Summary", heading1_style))
    risk_table_data = [
        ["Metric", "Value"],
        ["Total Attack Paths", str(total_paths)],
        ["Critical Paths", str(critical_paths)],
        ["High-Risk Paths", str(high_paths)],
        ["Average Risk Score", f"{avg_risk} / 100"],
        ["Exposed Hosts", str(len(hosts_set))],
        ["Unique CVEs", str(len(cve_set))],
        ["Remediation Actions Available", str(len(patches))],
    ]
    risk_table = Table(risk_table_data, colWidths=[9 * cm, 7 * cm])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), _SURFACE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _SURFACE]),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.4 * cm))

    # ---- Top Attack Paths ----
    story.append(Paragraph("Top Attack Paths", heading1_style))
    top_paths = sorted(paths, key=lambda p: p.get("risk_score", 0), reverse=True)[:10]

    if top_paths:
        path_table_data = [["Path ID", "Target", "Risk", "Severity", "Hops", "Detectability"]]
        for p in top_paths:
            path_table_data.append([
                p.get("id", "—"),
                p.get("target", "—"),
                str(p.get("risk_score", "—")),
                (p.get("severity") or "").upper(),
                str(len(p.get("hops", []))),
                (p.get("detectability") or "—").capitalize(),
            ])
        pt = Table(path_table_data, colWidths=[2.8 * cm, 3 * cm, 1.6 * cm, 2.4 * cm, 1.6 * cm, 3 * cm])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        # Colour severity cells
        for row_idx, p in enumerate(top_paths, start=1):
            sev = (p.get("severity") or "").lower()
            cell_color = _sev_color(sev)
            pt.setStyle(TableStyle([
                ("TEXTCOLOR", (3, row_idx), (3, row_idx), cell_color),
                ("FONTNAME", (3, row_idx), (3, row_idx), "Helvetica-Bold"),
            ]))
        story.append(pt)
    else:
        story.append(Paragraph("No attack paths available.", body_style))

    story.append(Spacer(1, 0.4 * cm))

    # ---- CVE / Vulnerability List ----
    story.append(Paragraph("Identified Vulnerabilities (CVEs)", heading1_style))
    cve_list = sorted(cve_set)
    if cve_list:
        for cve in cve_list:
            story.append(Paragraph(f"• {cve}", mono_style))
    else:
        story.append(Paragraph("No CVEs identified.", body_style))

    story.append(Spacer(1, 0.4 * cm))

    # ---- Remediation Recommendations ----
    story.append(Paragraph("Remediation Recommendations", heading1_style))
    sorted_patches = sorted(patches, key=lambda p: p.get("risk_reduction", 0), reverse=True)
    if sorted_patches:
        rem_data = [["CVE / Patch", "Target Host", "Paths Closed", "Risk Reduction", "Action"]]
        for patch in sorted_patches:
            rem_data.append([
                patch.get("vulnerability_id", "—"),
                patch.get("host", "—"),
                str(patch.get("paths_closed", "—")),
                f"-{patch.get('risk_reduction', 0)}%",
                Paragraph(patch.get("description", "")[:120], ParagraphStyle(
                    "small",
                    parent=styles["Normal"],
                    fontSize=7,
                    leading=9,
                )),
            ])
        rt = Table(rem_data, colWidths=[3.5 * cm, 3 * cm, 2 * cm, 2.5 * cm, 5 * cm])
        rt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(rt)
    else:
        story.append(Paragraph("No remediation patches available.", body_style))

    story.append(Spacer(1, 0.4 * cm))

    # ---- Detailed Path Entries ----
    story.append(Paragraph("Attack Path Details", heading1_style))
    for p in top_paths[:5]:
        story.append(Paragraph(
            f"<b>{p.get('id')}</b> → Target: <b>{p.get('target')}</b>  |  "
            f"Risk: <b>{p.get('risk_score')}</b>  |  Severity: <b>{(p.get('severity') or '').upper()}</b>",
            heading2_style,
        ))
        for hop in p.get("hops", []):
            story.append(Paragraph(
                f"  [{hop.get('host', '?')}] ({hop.get('ip', '')}) — "
                f"{hop.get('vulnerability', '')} / {hop.get('attack_technique', '')} — "
                f"{hop.get('description', '')}",
                mono_style,
            ))
        story.append(Spacer(1, 0.2 * cm))

    # ---- Footer note ----
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER, spaceBefore=12))
    story.append(Paragraph(
        f"AttackGraphX Platform  •  Confidential Security Assessment  •  {now}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#94a3b8")),
    ))

    doc.build(story)
    return buffer.getvalue()


# -----------------------------------------------------------------------
# CSV generation
# -----------------------------------------------------------------------

def generate_csv(paths: list) -> str:
    """
    Generate a structured CSV export from attack path data.
    Returns a UTF-8 string ready for StreamingResponse.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Header row
    writer.writerow([
        "Path_ID", "Target", "Risk_Score", "Severity", "Detectability",
        "Hop_Count", "Entry_Host", "Entry_IP", "Final_Host", "Final_IP",
        "CVEs", "ATT&CK_Techniques", "Hop_Chain",
    ])

    for p in paths:
        hops = p.get("hops", [])
        cves = "; ".join(h.get("vulnerability", "") for h in hops if h.get("vulnerability"))
        techniques = "; ".join(h.get("attack_technique", "") for h in hops if h.get("attack_technique"))
        hop_chain = " → ".join(h.get("host", "") for h in hops)
        entry = hops[0] if hops else {}
        final = hops[-1] if hops else {}

        writer.writerow([
            p.get("id", ""),
            p.get("target", ""),
            p.get("risk_score", ""),
            (p.get("severity") or "").upper(),
            p.get("detectability", ""),
            len(hops),
            entry.get("host", ""),
            entry.get("ip", ""),
            final.get("host", ""),
            final.get("ip", ""),
            cves,
            techniques,
            hop_chain,
        ])

    return output.getvalue()
