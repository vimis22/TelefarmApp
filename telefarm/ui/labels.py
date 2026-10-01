"""Visuel præsentation af domænebegreber: farver og badges (Streamlit-markdown)."""

from telefarm.domain import labels
from telefarm.domain.models import Decision, FindingCategory, Severity

SEVERITY_COLOR = {
    Severity.HIGH: "red",
    Severity.MODERATE: "orange",
    Severity.LOW: "blue",
}

DECISION_COLOR = {
    Decision.UNDECIDED: "gray",
    Decision.CONTINUE: "green",
    Decision.ADJUST: "orange",
    Decision.STOP: "red",
    Decision.MONITOR: "blue",
}

# Valgmulighederne i beslutningsknapperne; "Ikke besluttet" = intet valgt.
DECISION_OPTIONS = (Decision.CONTINUE, Decision.ADJUST, Decision.STOP, Decision.MONITOR)


def severity_badge(severity: Severity) -> str:
    return f":{SEVERITY_COLOR[severity]}-badge[{labels.SEVERITY[severity]}]"


def decision_badge(decision: Decision) -> str:
    return f":{DECISION_COLOR[decision]}-badge[{labels.DECISION[decision]}]"


def category_badge(category: FindingCategory) -> str:
    return f":gray-badge[{labels.CATEGORY[category]}]"


def escape_markdown(text: str) -> str:
    """Forhindrer at fx '*' eller '[' i lægemiddelnavne tolkes som formatering."""
    for char in "\\`*_[]<>#|~$":
        text = text.replace(char, "\\" + char)
    return text
