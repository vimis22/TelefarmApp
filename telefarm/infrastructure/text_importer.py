"""Fortolker tekst indsat fra FMK, journal og apotekssystem.

Én linje pr. post. Kolonner adskilles af tabulator (kopieret fra tabel), semikolon eller |.
Komma bruges ikke som separator, da det indgår i danske doser ("0,5 mg").
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime

from telefarm.application.dto import ImportResult, RawClinicalData
from telefarm.application.errors import ImportValidationError
from telefarm.domain.models import Diagnosis, Dispensing, Medication, Patient, RenalFunction, Sex

_SEPARATORS = ("\t", ";", "|")
_HEADER_WORDS = {"lægemiddel", "præparat", "navn", "kode", "diagnosekode", "dato", "udleveret"}
_ATC_PATTERN = re.compile(r"^[A-Z]\d{2}([A-Z]{1,2}(\d{2})?)?$")
_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%y", "%d.%m.%y")
_SEX_ALIASES = {
    "female": Sex.FEMALE, "kvinde": Sex.FEMALE, "k": Sex.FEMALE,
    "male": Sex.MALE, "mand": Sex.MALE, "m": Sex.MALE,
}


class TextClinicalDataImporter:
    def import_data(self, raw: RawClinicalData) -> ImportResult:
        warnings: list[str] = []
        medications = self._parse_medications(raw.medications_text, warnings)
        return ImportResult(
            patient=self._parse_patient(raw),
            renal_function=RenalFunction(
                creatinine_umol_l=_positive_or_none(raw.creatinine_umol_l),
                egfr_reported=_positive_or_none(raw.egfr_reported),
            ),
            medications=medications,
            diagnoses=self._parse_diagnoses(raw.diagnoses_text),
            dispensings=self._parse_dispensings(raw.dispensings_text, warnings),
            symptoms=parse_symptoms(raw.symptoms_text),
            warnings=warnings,
        )

    @staticmethod
    def _parse_patient(raw: RawClinicalData) -> Patient:
        pseudonym = raw.patient_pseudonym.strip()
        if not pseudonym:
            raise ImportValidationError("Angiv et patient-pseudonym (fx TF-024). Brug ikke CPR-nummer.")
        if re.fullmatch(r"\d{6}-?\d{4}", pseudonym):
            raise ImportValidationError("Pseudonymet ligner et CPR-nummer. Brug et pseudonym.")
        if raw.age is None or not 0 <= raw.age <= 130:
            raise ImportValidationError("Angiv patientens alder (0–130 år).")
        sex = _SEX_ALIASES.get(raw.sex.strip().lower())
        if sex is None:
            raise ImportValidationError("Angiv patientens køn.")
        return Patient(
            pseudonym=pseudonym,
            age=int(raw.age),
            sex=sex,
            weight_kg=_positive_or_none(raw.weight_kg),
        )

    @staticmethod
    def _parse_medications(text: str, warnings: list[str]) -> list[Medication]:
        medications: list[Medication] = []
        used_ids: set[str] = set()
        for line_number, cells in _rows(text):
            name, atc, strength, dosage, indication = (cells + [""] * 5)[:5]
            if not name:
                warnings.append(f"Ordination linje {line_number}: mangler lægemiddelnavn – sprunget over.")
                continue
            atc = atc.upper().replace(" ", "")
            if not atc:
                warnings.append(f"{name}: mangler ATC-kode – regler for præparatet kan ikke anvendes.")
            elif not _ATC_PATTERN.match(atc):
                warnings.append(f"{name}: ATC-koden '{atc}' er ugyldig – regler kan ikke anvendes.")
                atc = ""
            medications.append(Medication(
                id=_stable_id(f"{name}|{atc}|{strength}", used_ids),
                name=name,
                atc=atc,
                strength=strength,
                dosage=dosage,
                indication=indication,
            ))
        return medications

    @staticmethod
    def _parse_diagnoses(text: str) -> list[Diagnosis]:
        diagnoses = []
        for _, cells in _rows(text):
            if len(cells) == 1:
                diagnoses.append(Diagnosis(code="", text=cells[0]))
            else:
                diagnoses.append(Diagnosis(code=cells[0].upper(), text=cells[1]))
        return diagnoses

    @staticmethod
    def _parse_dispensings(text: str, warnings: list[str]) -> list[Dispensing]:
        dispensings = []
        for line_number, cells in _rows(text):
            date_text, name, atc, packages = (cells + [""] * 4)[:4]
            dispensed_on = parse_date(date_text)
            if dispensed_on is None or not name:
                warnings.append(f"Udlevering linje {line_number}: kræver dato og præparat – sprunget over.")
                continue
            dispensings.append(Dispensing(
                dispensed_on=dispensed_on,
                name=name,
                atc=atc.upper().replace(" ", ""),
                packages=int(packages) if packages.isdigit() else 1,
            ))
        return sorted(dispensings, key=lambda d: d.dispensed_on, reverse=True)


def parse_symptoms(text: str) -> list[str]:
    parts = re.split(r"[,;\n]", text)
    unique: dict[str, None] = {}
    for part in parts:
        symptom = part.strip().lower()
        if symptom:
            unique[symptom] = None
    return list(unique)


def parse_date(text: str) -> date | None:
    text = text.strip()
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def _rows(text: str) -> list[tuple[int, list[str]]]:
    """Returnerer (linjenummer, celler) for alle ikke-tomme linjer undtagen overskrifter."""
    rows = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        separator = next((s for s in _SEPARATORS if s in line), None)
        cells = [c.strip() for c in line.split(separator)] if separator else [line.strip()]
        if cells[0].lower() in _HEADER_WORDS:
            continue
        rows.append((line_number, cells))
    return rows


def _stable_id(key: str, used: set[str]) -> str:
    """Samme ordination får samme id ved genindlæsning, så beslutninger bevares."""
    base = "med-" + hashlib.sha1(key.lower().encode("utf-8")).hexdigest()[:8]
    candidate, counter = base, 2
    while candidate in used:
        candidate, counter = f"{base}-{counter}", counter + 1
    used.add(candidate)
    return candidate


def _positive_or_none(value: float | None) -> float | None:
    return value if value is not None and value > 0 else None
