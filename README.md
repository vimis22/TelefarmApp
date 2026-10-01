# TelefarmApp

Klinisk beslutningsstøtte til **Telefarmakologisk Ambulatorium (OUH · Klinisk Farmakologi, Region Syddanmark)**.
Systemet hjælper læger og farmaceuter med at gennemgå en patients samlede medicin og vurdere, om hvert
lægemiddel skal **fortsættes, justeres, seponeres eller monitoreres**.

> Reglerne og vidensgrundlaget i `r/data/` er **illustrative** og skal verificeres klinisk før brug.
> Data lever kun i brugerens session – intet gemmes permanent. Brug pseudonymer, aldrig CPR-numre.

## Kom i gang

```bash
pip install -r requirements.txt
streamlit run app.py
```

Kræver Python ≥ 3.11 og R ≥ 4.2 med pakken `jsonlite`. R findes automatisk (PATH eller
`C:\Program Files\R\R-*`); ellers sæt `TELEFARM_RSCRIPT` til stien til `Rscript.exe`.
Klik **Indsæt data → Indlæs fiktiv demo-patient TF-024** for at se et komplet eksempel.

## Arbejdsgang

1. **Indsæt data** – patient, kreatinin/eGFR og tekst kopieret fra FMK, journal og apotek.
2. **Gennemgå** – medicinliste, diagnoser, interaktioner og ACB, udleveringer, nyrefunktion og bivirkninger.
3. **Vælg fund** – markér de fund, der skal med i rapporten, og tilføj kliniske noter.
4. **Generér rapport** – Markdown-rapport med fund og beslutning pr. lægemiddel.

## Arkitektur

```
Streamlit UI ──► Application (use cases) ──► Domain (rene modeller)
                      │ afhænger kun af porte (Protocols)
                      ▼
                Infrastructure ──► Rscript ──► R-regelmotor (JSON ind/ud)
```

Afhængigheder peger kun indad. Al klinisk logik ligger i R; Python står for brugerflade,
sessionstilstand, tekstimport og rapport.

| Mappe | Ansvar |
|---|---|
| `telefarm/domain/` | Kliniske begreber (`Review`, `Finding`, `Medication` …) og danske betegnelser. Ingen afhængigheder. |
| `telefarm/application/` | Use cases (`ReviewService`), porte (`ports.py`), DTO'er og fejltyper. |
| `telefarm/infrastructure/` | Adaptere: R-motoren, FMK-tekstimport, Markdown-rapport, demo-patient. |
| `telefarm/ui/` | Streamlit: `app_shell` (ramme), `navigation`, `state` (eneste adgang til session state), `components/` og én fil pr. side i `views/`. |
| `telefarm/bootstrap.py` | Composition root – kobler adaptere på use cases. |
| `r/engine.R` | Indgang: læser JSON fra stdin, skriver JSON til stdout. |
| `r/R/` | Én fil pr. klinisk regel: `renal`, `acb`, `interactions`, `disease_drug`, `adherence`, `adverse_effects`, `indication`. |
| `r/data/` | Vidensgrundlag som semikolonseparerede CSV-filer. |

### Tilføj en ny klinisk regel

1. Opret `r/R/min_regel.R` med en funktion der returnerer en liste af `new_finding(...)`.
2. Læg eventuelle data i `r/data/min_regel.csv` og indlæs dem i `load_knowledge_base()` (`r/R/io.R`).
3. Kald funktionen fra `analyse_review()` i `r/R/analysis.R`.
4. Ny kategori? Tilføj den i `CATEGORIES` (`r/R/utils.R`), `FindingCategory` og `labels.CATEGORY`,
   og knyt den til en side i `telefarm/ui/routing.py`.

### JSON-kontrakt mellem Python og R

Request: `reference_date`, `patient`, `renal_function`, `medications[]`, `diagnoses[]`,
`dispensings[]`, `symptoms[]`. Response: `egfr` (eller `null`), `acb {total, items[]}` og
`findings[]` med `id, category, severity, title, description, recommendation,
suggested_decision, medication_ids[]`. Se `_to_payload`/`_from_payload` i
`telefarm/infrastructure/r_clinical_engine.py`.

## Test

```bash
python -m pytest                                   # Python: domæne, use cases, import, R-integration og UI
Rscript --vanilla tests/r/test_rules.R             # R: de kliniske regler
```

Integrations- og UI-testene springes over, hvis R ikke er installeret.
