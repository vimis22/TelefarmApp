"""Trinindikator for arbejdsgangen: Indsæt data → Gennemgå → Vælg fund → Generér rapport."""

from __future__ import annotations

import streamlit as st

from telefarm.domain.models import Review
from telefarm.ui.routing import WorkflowStep


def completed_steps(review: Review) -> set[WorkflowStep]:
    done = set()
    if review.has_data:
        done.add(WorkflowStep.INSERT)
    if review.analysis is not None:
        done.add(WorkflowStep.REVIEW)
    if review.selected_finding_ids:
        done.add(WorkflowStep.SELECT)
    if review.report is not None:
        done.add(WorkflowStep.REPORT)
    return done


def render(current: WorkflowStep, review: Review) -> None:
    done = completed_steps(review)
    items = []
    for step in WorkflowStep:
        modifier = "current" if step == current else "done" if step in done else "todo"
        marker = "✓" if modifier == "done" else str(step.value)
        items.append(
            f'<div class="tf-step tf-step--{modifier}">'
            f'<span class="tf-step__marker">{marker}</span><span>{step.label}</span></div>'
        )
    st.html(f'<nav class="tf-stepper" aria-label="Arbejdsgang">{"".join(items)}</nav>')
