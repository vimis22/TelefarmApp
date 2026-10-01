"""Danner gennemgangens konklusion som Markdown, klar til journal eller e-mail."""

from __future__ import annotations

from datetime import date

from telefarm.domain import labels
from telefarm.domain.models import Finding, Report, Review

_DISCLAIMER = (
    "Rapporten er dannet af et beslutningsstøttesystem. Fund og forslag skal vurderes "
    "klinisk af den ansvarlige læge, før behandlingen ændres."
)


class MarkdownReportRenderer:
    def render(self, review: Review, generated_on: date) -> Report:
        if review.patient is None:
            raise ValueError("Rapporten kræver patientoplysninger.")
        sections = [
            self._header(review, generated_on),
            self._findings(review),
            self._decisions(review),
            f"---\n\n_{_DISCLAIMER}_\n",
        ]
        return Report(
            content="\n".join(sections),
            file_name=f"medicingennemgang_{review.patient.pseudonym}_{generated_on.isoformat()}.md",
            mime_type="text/markdown",
        )

    @staticmethod
    def _header(review: Review, generated_on: date) -> str:
        patient = review.patient
        analysis = review.analysis
        egfr = analysis.egfr if analysis else None
        egfr_text = (
            f"{egfr.value:.0f} mL/min/1,73 m² ({labels.EGFR_SOURCE[egfr.source]}, {egfr.ckd_stage})"
            if egfr else "ikke oplyst"
        )
        lines = [
            f"# Medicingennemgang – Patient {patient.pseudonym}",
            "",
            f"**Dato:** {generated_on.strftime('%d-%m-%Y')}  ",
            f"**Patient:** {patient.age} år, {labels.SEX[patient.sex].lower()}  ",
            f"**Antal lægemidler:** {len(review.medications)}  ",
            f"**Nyrefunktion (eGFR):** {egfr_text}  ",
            f"**Antikolinerg byrde (ACB):** {analysis.acb_total if analysis else 0}",
            "",
        ]
        if review.is_demo:
            lines += ["> Fiktiv patient – kliniske fund, scores og kildedata er illustrative.", ""]
        return "\n".join(lines)

    def _findings(self, review: Review) -> str:
        findings = review.selected_findings
        lines = [f"## Udvalgte fund ({len(findings)})", ""]
        if not findings:
            lines += ["Ingen fund er valgt til rapporten.", ""]
        for number, finding in enumerate(findings, start=1):
            lines += self._finding(review, number, finding)
        return "\n".join(lines)

    @staticmethod
    def _finding(review: Review, number: int, finding: Finding) -> list[str]:
        lines = [
            f"### {number}. {finding.title}",
            "",
            f"**Alvorlighed:** {labels.SEVERITY[finding.severity]} · "
            f"**Kategori:** {labels.CATEGORY[finding.category]} · "
            f"**Forslag:** {labels.SUGGESTION[finding.suggested_decision]}",
            "",
            finding.description,
            "",
            f"**Anbefaling:** {finding.recommendation}",
        ]
        medication_names = review.medication_names(finding.medication_ids)
        if medication_names:
            lines.append(f"  \n**Berørte lægemidler:** {', '.join(medication_names)}")
        note = review.finding_notes.get(finding.id)
        if note:
            lines.append(f"  \n**Klinisk note:** {note}")
        return lines + [""]

    @staticmethod
    def _decisions(review: Review) -> str:
        lines = [
            "## Beslutninger pr. lægemiddel",
            "",
            "| Lægemiddel | Dosering | Beslutning | Note |",
            "|---|---|---|---|",
        ]
        for medication in review.medications:
            decision = review.decision_for(medication.id)
            cells = [medication.display_name, medication.dosage,
                     labels.DECISION[decision.decision], decision.note]
            lines.append("| " + " | ".join(_table_cell(c) for c in cells) + " |")
        return "\n".join(lines) + "\n"


def _table_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ") or "–"
