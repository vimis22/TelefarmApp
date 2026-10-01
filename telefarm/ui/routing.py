"""Sider, arbejdsgangens trin og navigation mellem siderne."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from telefarm.domain.models import FindingCategory

_PAGES_KEY = "telefarm.pages"


class PageKey(StrEnum):
    """Værdien bruges som url-sti."""

    OVERVIEW = "patientoverblik"
    INSERT = "indsaet-data"
    MEDICATIONS = "medicinliste"
    DIAGNOSES = "diagnoser"
    INTERACTIONS = "interaktioner-og-acb"
    DISPENSINGS = "apoteksudleveringer"
    RENAL = "nyrefunktion"
    ADVERSE_EFFECTS = "bivirkninger"
    REPORT = "rapportbygger"


class WorkflowStep(IntEnum):
    INSERT = 1
    REVIEW = 2
    SELECT = 3
    REPORT = 4

    @property
    def label(self) -> str:
        return {1: "Indsæt data", 2: "Gennemgå", 3: "Vælg fund", 4: "Generér rapport"}[self.value]


@dataclass(frozen=True)
class PageSpec:
    key: PageKey
    title: str
    icon: str
    section: str
    categories: tuple[FindingCategory, ...] = ()


PAGES: tuple[PageSpec, ...] = (
    PageSpec(PageKey.OVERVIEW, "Patientoverblik", ":material/dashboard:", "Patient og data"),
    PageSpec(PageKey.INSERT, "Indsæt data", ":material/content_paste:", "Patient og data"),
    PageSpec(PageKey.MEDICATIONS, "Medicinliste", ":material/pill:", "Gennemgang",
             (FindingCategory.INDICATION,)),
    PageSpec(PageKey.DIAGNOSES, "Diagnoser", ":material/checklist:", "Gennemgang",
             (FindingCategory.DIAGNOSIS,)),
    PageSpec(PageKey.INTERACTIONS, "Interaktioner og ACB", ":material/schema:", "Gennemgang",
             (FindingCategory.INTERACTION, FindingCategory.ACB)),
    PageSpec(PageKey.DISPENSINGS, "Apoteksudleveringer", ":material/deployed_code:", "Gennemgang",
             (FindingCategory.ADHERENCE,)),
    PageSpec(PageKey.RENAL, "Nyrefunktion", ":material/monitor_heart:", "Gennemgang",
             (FindingCategory.RENAL,)),
    PageSpec(PageKey.ADVERSE_EFFECTS, "Bivirkninger", ":material/search:", "Gennemgang",
             (FindingCategory.ADVERSE_EFFECT,)),
    PageSpec(PageKey.REPORT, "Rapportbygger", ":material/co_present:", "Rapport"),
)

REVIEW_PAGES = tuple(p for p in PAGES if p.categories)


def spec(key: PageKey) -> PageSpec:
    return next(p for p in PAGES if p.key == key)


def register(pages: dict[PageKey, StreamlitPage]) -> None:
    st.session_state[_PAGES_KEY] = pages


def go_to(key: PageKey) -> None:
    """Skifter side. Må kun kaldes fra script-flowet, ikke fra on_click-callbacks."""
    st.switch_page(st.session_state[_PAGES_KEY][key])
