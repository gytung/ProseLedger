"""Read and export proposal outputs without running a model."""

import html
import io
import json
from pathlib import Path
import re
import streamlit as st
from .jobs import read_json

BRANCHES = {"targeted": "Targeted", "planner": "Planner-only", "memory": "Memory"}


def score(value) -> float:
    if isinstance(value, dict):
        return float(value.get("score", value.get("severity", 0)))
    return float(value or 0)


@st.cache_data(show_spinner=False)
def proposal_pdf(text: str, label: str, references_json: str) -> bytes | None:
    """Portable English PDF using PDF-standard Times faces; no external fonts."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    except ImportError:
        return None
    output = io.BytesIO()
    styles = {
        "body": ParagraphStyle(
            "body",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=14.7,
            spaceAfter=7,
            textColor=colors.HexColor("#393447"),
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Times-Bold",
            fontSize=19,
            leading=23,
            spaceAfter=18,
            textColor=colors.HexColor("#67517B"),
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName="Times-Bold",
            fontSize=13,
            leading=17,
            spaceBefore=10,
            spaceAfter=7,
            textColor=colors.HexColor("#67517B"),
        ),
        "small": ParagraphStyle(
            "small",
            fontName="Times-Italic",
            fontSize=8.5,
            leading=11.2,
            spaceAfter=9,
            textColor=colors.HexColor("#7B7186"),
        ),
    }
    story = [Paragraph(f"ProseLedger · {html.escape(label)}", styles["small"])]
    paragraphs = re.split(r"\n\s*\n", text.strip())
    for index, block in enumerate(paragraphs):
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("#"):
            line = re.sub(r"^#+\s*", "", lines[0])
            story.append(Paragraph(html.escape(line), styles["heading"]))
            lines = lines[1:]
            if not lines:
                continue
            block = " ".join(lines)
        elif index == 0 and len(block) < 250:
            story.append(Paragraph(html.escape(block), styles["title"]))
            continue
        escaped = html.escape(block.replace("\n", " "))
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", escaped)
        story.append(Paragraph(escaped, styles["body"]))
    references = json.loads(references_json)
    if references:
        story += [Spacer(1, 8), Paragraph("Supplied references", styles["heading"])]
        for source in references:
            line = f"[{source.get('id', '')}] {source.get('title', '')}"
            if source.get("year"):
                line += f" ({source['year']})."
            if source.get("url"):
                line += " " + source["url"]
            story.append(Paragraph(html.escape(line), styles["small"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#8A7C98"))
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(46, 30, "ProseLedger · Research proposal · Generated text for review")
        canvas.drawRightString(A4[0] - 46, 30, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=46,
        leftMargin=46,
        topMargin=42,
        bottomMargin=48,
        title=f"ProseLedger: {label}",
        author="ProseLedger · Group 18",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


def source_table(sources: list):
    for index, source in enumerate(sources, 1):
        title = source.get("title", f"Source {index}")
        source_id = source.get("id", f"S{index}")
        year = source.get("year", "")
        url = source.get("url", "")
        if url.startswith(("https://", "http://")):
            st.markdown(f"**[{source_id}] [{title}]({url})**" + (f" · {year}" if year else ""))
        else:
            st.markdown(f"**[{source_id}] {title}**" + (f" · {year}" if year else ""))
    st.caption(
        "Only supplied text is used as evidence; source excerpts do not constitute full-text literature coverage."
    )


def heading(kicker: str, title: str, description: str):
    st.markdown(f'<div class="eyebrow">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="intro">{html.escape(description)}</div>', unsafe_allow_html=True)


def live_summary(summary: dict, output: Path):
    branches = summary.get("branches", {})
    if not branches:
        return
    cols = st.columns(3)
    for i, (key, label) in enumerate(BRANCHES.items()):
        branch = branches.get(key, {})
        if branch.get("final_score") is not None:
            cols[i].metric(label, f"{score(branch['final_score']):.1f}")
        raw_path = branch.get("final_text_path", "")
        if raw_path:
            path = Path(raw_path)
            if not path.is_absolute():
                path = output / path
            try:
                path.resolve().relative_to(output.resolve())
            except ValueError:
                continue
            if path.exists():
                text = path.read_text(encoding="utf-8")
                references = read_json(output.parent / "supplied_sources.json", [])
                pdf = proposal_pdf(text, label, json.dumps(references, ensure_ascii=False))
                if pdf:
                    cols[i].download_button(
                        f"Download {label} PDF",
                        pdf,
                        file_name=f"proposal_{key}.pdf",
                        mime="application/pdf",
                        key=f"live_pdf_{output.name}_{key}",
                    )
                cols[i].download_button(
                    f"Download {label}",
                    text,
                    file_name=f"proposal_{key}.md",
                    key=f"live_{output.name}_{key}",
                )
                with st.expander(f"Read new {label} proposal"):
                    st.markdown(text)
    st.caption(
        "Lower scores are better. A new model run can produce different scores from the archived evaluation."
    )
