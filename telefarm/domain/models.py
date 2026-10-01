"""Domænemodeller for en klinisk medicingennemgang.

Rene datastrukturer uden afhængigheder til UI, R eller filsystem, så de
kliniske begreber kan genbruges og testes isoleret.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"


class Severity(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

    @property
    def rank(self) -> int:          # 0 = mest alvorlig, bruges til sortering
        return list(Severity).index(self)


class Decision(StrEnum):
    UNDECIDED = "undecided"
    CONTINUE = "continue"
    ADJUST = "adjust"
    STOP = "stop"
    MONITOR = "monitor"


class FindingCategory(StrEnum):
    INDICATION = "indication"
    RENAL = "renal"
    ACB = "acb"
    INTERACTION = "interaction"
    DIAGNOSIS = "diagnosis"
    ADHERENCE = "adherence"
    ADVERSE_EFFECT = "adverse_effect"


class EgfrSource(StrEnum):
    REPORTED = "reported"
    CKD_EPI_2021 = "ckd_epi_2021"


@dataclass(frozen=True)
class Patient:
    pseudonym: str
    age: int
    sex: Sex
    weight_kg: float | None = None


@dataclass(frozen=True)
class Medication:
    id: str
    name: str
    atc: str
    strength: str = ""
    dosage: str = ""
    indication: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.name} {self.strength}".strip()


@dataclass(frozen=True)
class Diagnosis:
    code: str
    text: str


@dataclass(frozen=True)
class Dispensing:
    dispensed_on: date
    name: str
    atc: str
    packages: int = 1


@dataclass(frozen=True)
class RenalFunction:
    creatinine_umol_l: float | None = None
    egfr_reported: float | None = None      # mL/min/1,73 m²


@dataclass(frozen=True)
class ClinicalInput:
    """Det samlede datagrundlag, som den kliniske regelmotor analyserer."""

    patient: Patient
    medications: tuple[Medication, ...]
    diagnoses: tuple[Diagnosis, ...]
    dispensings: tuple[Dispensing, ...]
    symptoms: tuple[str, ...]
    renal_function: RenalFunction
    reference_date: date


@dataclass(frozen=True)
class Finding:
    id: str
    category: FindingCategory
    severity: Severity
    title: str
    description: str
    recommendation: str
    suggested_decision: Decision
    medication_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EgfrResult:
    value: float
    source: EgfrSource

    @property
    def ckd_stage(self) -> str:
        """KDIGO GFR-kategori (G1–G5)."""
        for limit, stage in ((90, "G1"), (60, "G2"), (45, "G3a"), (30, "G3b"), (15, "G4")):
            if self.value >= limit:
                return stage
        return "G5"


@dataclass(frozen=True)
class AcbItem:
    medication_id: str
    score: int


@dataclass(frozen=True)
class AnalysisResult:
    egfr: EgfrResult | None
    acb_items: tuple[AcbItem, ...]
    findings: tuple[Finding, ...]

    @property
    def acb_total(self) -> int:
        return sum(item.score for item in self.acb_items)

    def finding(self, finding_id: str) -> Finding | None:
        return next((f for f in self.findings if f.id == finding_id), None)

    def findings_in(self, *categories: FindingCategory) -> list[Finding]:
        matches = [f for f in self.findings if f.category in categories]
        return sorted(matches, key=lambda f: f.severity.rank)

    def findings_for_medication(self, medication_id: str) -> list[Finding]:
        matches = [f for f in self.findings if medication_id in f.medication_ids]
        return sorted(matches, key=lambda f: f.severity.rank)

    def suggested_decision_for(self, medication_id: str) -> Decision:
        """Forslaget fra det mest alvorlige fund, der har en konkret beslutning."""
        for finding in self.findings_for_medication(medication_id):
            if finding.suggested_decision is not Decision.UNDECIDED:
                return finding.suggested_decision
        return Decision.UNDECIDED

    def acb_score_for(self, medication_id: str) -> int:
        return next((i.score for i in self.acb_items if i.medication_id == medication_id), 0)


@dataclass
class MedicationDecision:
    decision: Decision = Decision.UNDECIDED
    note: str = ""


@dataclass(frozen=True)
class Report:
    content: str
    file_name: str
    mime_type: str


@dataclass
class Review:
    """Aggregat for én gennemgang – lever kun i sessionen."""

    patient: Patient | None = None
    medications: list[Medication] = field(default_factory=list)
    diagnoses: list[Diagnosis] = field(default_factory=list)
    dispensings: list[Dispensing] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    renal_function: RenalFunction = field(default_factory=RenalFunction)
    is_demo: bool = False
    analysis: AnalysisResult | None = None
    selected_finding_ids: set[str] = field(default_factory=set)
    finding_notes: dict[str, str] = field(default_factory=dict)
    medication_decisions: dict[str, MedicationDecision] = field(default_factory=dict)
    report: Report | None = None

    @property
    def has_data(self) -> bool:
        return self.patient is not None

    @property
    def findings(self) -> tuple[Finding, ...]:
        return self.analysis.findings if self.analysis else ()

    @property
    def selected_findings(self) -> list[Finding]:
        selected = [f for f in self.findings if f.id in self.selected_finding_ids]
        return sorted(selected, key=lambda f: f.severity.rank)

    def medication(self, medication_id: str) -> Medication | None:
        return next((m for m in self.medications if m.id == medication_id), None)

    def medication_names(self, medication_ids: tuple[str, ...]) -> list[str]:
        return [m.name for m in map(self.medication, medication_ids) if m is not None]

    def decision_for(self, medication_id: str) -> MedicationDecision:
        return self.medication_decisions.get(medication_id, MedicationDecision())

    def last_dispensing_for(self, medication: Medication) -> Dispensing | None:
        matches = [
            d for d in self.dispensings
            if (medication.atc and d.atc == medication.atc)
            or d.name.split(" ")[0].lower() == medication.name.split(" ")[0].lower()
        ]
        return max(matches, key=lambda d: d.dispensed_on, default=None)

    def to_clinical_input(self, reference_date: date) -> ClinicalInput:
        if self.patient is None:
            raise ValueError("Der kan ikke analyseres uden patientoplysninger.")
        return ClinicalInput(
            patient=self.patient,
            medications=tuple(self.medications),
            diagnoses=tuple(self.diagnoses),
            dispensings=tuple(self.dispensings),
            symptoms=tuple(self.symptoms),
            renal_function=self.renal_function,
            reference_date=reference_date,
        )
