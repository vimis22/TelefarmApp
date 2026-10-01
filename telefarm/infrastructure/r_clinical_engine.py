"""Adapter der lader R-regelmotoren (r/engine.R) implementere porten ClinicalEngine.

Kommunikation sker med JSON over stdin/stdout. Al oversættelse mellem JSON og
domænemodeller ligger i denne fil.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from telefarm.application.errors import ClinicalEngineError
from telefarm.domain.models import (
    AcbItem,
    AnalysisResult,
    ClinicalInput,
    Decision,
    EgfrResult,
    EgfrSource,
    Finding,
    FindingCategory,
    Severity,
)


class RScriptClinicalEngine:
    def __init__(self, rscript: Path | None, engine_script: Path, timeout_seconds: float = 30):
        self._rscript = rscript
        self._engine_script = engine_script
        self._timeout = timeout_seconds

    def analyse(self, clinical_input: ClinicalInput) -> AnalysisResult:
        if self._rscript is None:
            raise ClinicalEngineError(
                "R blev ikke fundet. Installér R eller sæt miljøvariablen TELEFARM_RSCRIPT "
                "til stien til Rscript.exe."
            )
        command = [str(self._rscript), "--vanilla", str(self._engine_script)]
        try:
            completed = subprocess.run(
                command, input=json.dumps(_to_payload(clinical_input)),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=self._timeout, check=False,
            )
        except FileNotFoundError as exc:
            raise ClinicalEngineError(f"Rscript blev ikke fundet: {self._rscript}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ClinicalEngineError("R-regelmotoren svarede ikke i tide.") from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip()[-500:] or "ukendt fejl"
            raise ClinicalEngineError(f"R-regelmotoren fejlede: {detail}")
        try:
            return _from_payload(json.loads(completed.stdout))
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise ClinicalEngineError("R-regelmotoren returnerede et ugyldigt svar.") from exc


def _to_payload(clinical_input: ClinicalInput) -> dict[str, Any]:
    patient = clinical_input.patient
    renal = clinical_input.renal_function
    return {
        "reference_date": clinical_input.reference_date.isoformat(),
        "patient": {"age": patient.age, "sex": patient.sex.value, "weight_kg": patient.weight_kg},
        "renal_function": {
            "creatinine_umol_l": renal.creatinine_umol_l,
            "egfr_reported": renal.egfr_reported,
        },
        "medications": [
            {"id": m.id, "name": m.name, "atc": m.atc, "strength": m.strength,
             "dosage": m.dosage, "indication": m.indication}
            for m in clinical_input.medications
        ],
        "diagnoses": [{"code": d.code, "text": d.text} for d in clinical_input.diagnoses],
        "dispensings": [
            {"dispensed_on": d.dispensed_on.isoformat(), "name": d.name, "atc": d.atc,
             "packages": d.packages}
            for d in clinical_input.dispensings
        ],
        "symptoms": list(clinical_input.symptoms),
    }


def _from_payload(payload: dict[str, Any]) -> AnalysisResult:
    egfr = payload.get("egfr")
    return AnalysisResult(
        egfr=EgfrResult(value=float(egfr["value"]), source=EgfrSource(egfr["source"])) if egfr else None,
        acb_items=tuple(
            AcbItem(medication_id=item["medication_id"], score=int(item["score"]))
            for item in payload["acb"]["items"]
        ),
        findings=tuple(_finding_from_payload(f) for f in payload["findings"]),
    )


def _finding_from_payload(item: dict[str, Any]) -> Finding:
    return Finding(
        id=item["id"],
        category=FindingCategory(item["category"]),
        severity=Severity(item["severity"]),
        title=item["title"],
        description=item["description"],
        recommendation=item["recommendation"],
        suggested_decision=Decision(item["suggested_decision"]),
        medication_ids=tuple(item.get("medication_ids") or ()),
    )
