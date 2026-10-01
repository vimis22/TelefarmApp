"""Danske betegnelser for domænebegreberne.

Deles af brugerfladen og rapporten, så samme ord bruges begge steder.
"""

from telefarm.domain.models import Decision, EgfrSource, FindingCategory, Severity, Sex

SEVERITY = {
    Severity.HIGH: "Høj",
    Severity.MODERATE: "Moderat",
    Severity.LOW: "Lav",
}

DECISION = {
    Decision.UNDECIDED: "Ikke besluttet",
    Decision.CONTINUE: "Fortsæt",
    Decision.ADJUST: "Justér",
    Decision.STOP: "Seponér",
    Decision.MONITOR: "Monitorér",
}

# Et fund uden konkret beslutning kræver klinisk afklaring.
SUGGESTION = {**DECISION, Decision.UNDECIDED: "Afklar"}

CATEGORY = {
    FindingCategory.INDICATION: "Indikation",
    FindingCategory.RENAL: "Nyrefunktion",
    FindingCategory.ACB: "Antikolinerg byrde",
    FindingCategory.INTERACTION: "Interaktion",
    FindingCategory.DIAGNOSIS: "Diagnose",
    FindingCategory.ADHERENCE: "Adhærens",
    FindingCategory.ADVERSE_EFFECT: "Bivirkning",
}

SEX = {Sex.FEMALE: "Kvinde", Sex.MALE: "Mand"}

EGFR_SOURCE = {
    EgfrSource.REPORTED: "oplyst",
    EgfrSource.CKD_EPI_2021: "beregnet, CKD-EPI 2021",
}
