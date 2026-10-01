# Indikation: manglende indikation, dobbeltbehandling og polyfarmaci.

POLYPHARMACY_THRESHOLD <- 10

indication_findings <- function(meds) {
  if (nrow(meds) == 0) return(list())
  c(missing_indication_findings(meds), duplicate_therapy_findings(meds), polypharmacy_findings(meds))
}

missing_indication_findings <- function(meds) {
  missing <- meds[vapply(meds$indication, is_blank, logical(1)), ]
  lapply(seq_len(nrow(missing)), function(i) {
    med <- missing[i, ]
    new_finding(
      id = paste0("indication:missing:", med$id),
      category = "indication",
      severity = "low",
      title = sprintf("Manglende indikation: %s", med$name),
      description = sprintf("Der er ikke angivet en indikation for %s.", medication_label(med)),
      recommendation = "Afklar indikationen. Uden aktuel indikation bør seponering overvejes.",
      decision = "undecided",
      medication_ids = med$id
    )
  })
}

# Samme kemiske undergruppe (ATC niveau 4, fem tegn) to gange tyder på dobbeltbehandling.
duplicate_therapy_findings <- function(meds) {
  with_atc <- meds[nchar(meds$atc) >= 5, ]
  groups <- substr(with_atc$atc, 1, 5)
  duplicated_groups <- unique(groups[duplicated(groups)])
  lapply(duplicated_groups, function(group) {
    members <- with_atc[groups == group, ]
    new_finding(
      id = paste0("indication:duplicate:", group),
      category = "indication",
      severity = "moderate",
      title = sprintf("Mulig dobbeltbehandling (%s)", group),
      description = sprintf("%s tilhører samme lægemiddelgruppe.", join_names(members$name)),
      recommendation = "Vurdér om begge præparater er nødvendige.",
      decision = "adjust",
      medication_ids = members$id
    )
  })
}

polypharmacy_findings <- function(meds) {
  if (nrow(meds) < POLYPHARMACY_THRESHOLD) return(list())
  list(new_finding(
    id = "indication:polypharmacy",
    category = "indication",
    severity = "low",
    title = sprintf("Polyfarmaci (%d lægemidler)", nrow(meds)),
    description = sprintf("Patienten er i behandling med %d lægemidler. Risikoen for interaktioner og bivirkninger stiger med antallet.", nrow(meds)),
    recommendation = "Gennemgå systematisk om hvert præparat fortsat har en aktuel indikation og en gunstig nytte/risiko-balance.",
    decision = "undecided"
  ))
}
