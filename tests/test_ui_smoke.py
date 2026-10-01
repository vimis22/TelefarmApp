"""Røgtest af brugerfladen med Streamlits AppTest (ingen browser nødvendig)."""

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from telefarm.config import PROJECT_ROOT, Settings
from telefarm.ui.routing import PAGES, PageKey

requires_r = pytest.mark.skipif(Settings.from_environment().rscript_path is None,
                                reason="Rscript er ikke installeret")


def new_app() -> AppTest:
    return AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=60).run()


def open_page(app: AppTest, key: PageKey) -> AppTest:
    # AppTest.switch_page understøtter kun filbaserede sider. st.Page identificerer
    # en side ved hash af url_path, så vi sætter den direkte.
    app._page_hash = calc_hash(key.value)
    return app.run()


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.key.value)
def test_every_page_renders_without_data(page):
    app = open_page(new_app(), page.key)
    assert not app.exception


def test_empty_medication_list_shows_empty_state():
    app = open_page(new_app(), PageKey.MEDICATIONS)
    assert any("Ingen medicinliste" in m.value for m in app.markdown)
    assert any(b.label == "Indsæt ordinationer" for b in app.button)


@requires_r
def test_demo_patient_flow_through_all_pages():
    app = open_page(new_app(), PageKey.INSERT)
    next(b for b in app.button if "demo-patient" in b.label).click().run()
    assert not app.exception

    review = app.session_state["telefarm.review"]
    assert len(review.medications) == 12
    assert review.analysis.egfr.value == 38

    for page in PAGES:
        open_page(app, page.key)
        assert not app.exception, page.key

    open_page(app, PageKey.REPORT)
    next(b for b in app.button if b.label == "Vælg alle høje").click().run()
    next(b for b in app.button if b.label == "Generér rapport").click().run()
    assert not app.exception
    review = app.session_state["telefarm.review"]
    assert review.selected_finding_ids and review.report is not None
