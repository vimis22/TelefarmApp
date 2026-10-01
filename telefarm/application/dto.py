"""Dataoverførselsobjekter mellem brugerflade og use cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from telefarm.domain.models import Diagnosis, Dispensing, Medication, Patient, RenalFunction


@dataclass(frozen=True)
class RawClinicalData:
    """Ubehandlet input som brugeren indsætter (fx kopieret fra FMK)."""

    patient_pseudonym: str = ""
    age: int | None = None
    sex: str = ""
    weight_kg: float | None = None
    creatinine_umol_l: float | None = None
    egfr_reported: float | None = None
    medications_text: str = ""
    diagnoses_text: str = ""
    dispensings_text: str = ""
    symptoms_text: str = ""


@dataclass(frozen=True)
class ImportResult:
    patient: Patient
    renal_function: RenalFunction
    medications: list[Medication]
    diagnoses: list[Diagnosis]
    dispensings: list[Dispensing]
    symptoms: list[str]
    warnings: list[str] = field(default_factory=list)
