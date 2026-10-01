"""Fiktiv demo-patient TF-024 til undervisning og afprøvning.

Datoerne beregnes relativt til i dag, så adhærensfundene altid ser ens ud.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

from telefarm.application.dto import RawClinicalData

_MEDICATIONS = """\
Lægemiddel; ATC; Styrke; Dosering; Indikation
Metformin; A10BA02; 500 mg; 1 tablet 3 gange dagligt; Type 2-diabetes
Ibuprofen; M01AE01; 400 mg; 1 tablet 3 gange dagligt; Knæsmerter
Apixaban; B01AF02; 5 mg; 1 tablet 2 gange dagligt; Atrieflimren
Ramipril; C09AA05; 5 mg; 1 tablet dagligt; Hjertesvigt
Furosemid; C03CA01; 40 mg; 1 tablet morgen; Hjertesvigt
Digoxin; C01AA05; 62,5 mikrogram; 1 tablet dagligt; Atrieflimren
Simvastatin; C10AA01; 40 mg; 1 tablet aften; Hyperkolesterolæmi
Amitriptylin; N06AA09; 25 mg; 1 tablet til natten; Polyneuropati
Oxybutynin; G04BD04; 5 mg; 1 tablet 2 gange dagligt; Urininkontinens
Zopiclon; N05CF01; 7,5 mg; 1 tablet til natten; Søvnbesvær
Pantoprazol; A02BC02; 40 mg; 1 tablet dagligt;
Paracetamol; N02BE01; 1 g; 2 tabletter 3 gange dagligt; Smerter
"""

_DIAGNOSES = """\
Kode; Diagnose
DE11.9; Type 2-diabetes
DI50.9; Hjertesvigt
DI48.9; Atrieflimren
DE78.0; Hyperkolesterolæmi
DG62.9; Polyneuropati
DN39.4; Urininkontinens
DR29.6; Tendens til fald
"""

# (dage siden udlevering, præparat, ATC)
_DISPENSINGS = [
    (28, "Metformin", "A10BA02"),
    (35, "Ibuprofen", "M01AE01"),
    (21, "Apixaban", "B01AF02"),
    (60, "Ramipril", "C09AA05"),
    (60, "Furosemid", "C03CA01"),
    (45, "Digoxin", "C01AA05"),
    (210, "Simvastatin", "C10AA01"),
    (50, "Amitriptylin", "N06AA09"),
    (14, "Zopiclon", "N05CF01"),
    (90, "Pantoprazol", "A02BC02"),
    (30, "Paracetamol", "N02BE01"),
    (40, "Tramadol", "N02AX02"),
    (120, "Metformin", "A10BA02"),
    (125, "Apixaban", "B01AF02"),
]


class DemoPatientSource:
    def __init__(self, clock: Callable[[], date] = date.today):
        self._clock = clock

    def load(self) -> RawClinicalData:
        today = self._clock()
        dispensings = "\n".join(
            f"{(today - timedelta(days=days)).strftime('%d-%m-%Y')}; {name}; {atc}; 1"
            for days, name, atc in sorted(_DISPENSINGS)
        )
        return RawClinicalData(
            patient_pseudonym="TF-024",
            age=78,
            sex="female",
            weight_kg=64,
            creatinine_umol_l=125,
            medications_text=_MEDICATIONS,
            diagnoses_text=_DIAGNOSES,
            dispensings_text="Dato; Præparat; ATC; Pakninger\n" + dispensings,
            symptoms_text="Svimmelhed, mundtørhed, obstipation, fald",
        )
