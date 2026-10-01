# Orkestrering: kører alle kliniske regler på én forespørgsel.
# En ny regel tilføjes ved at lave et nyt modul og kalde det herfra.

analyse_review <- function(request, kb) {
  meds        <- as_table(request$medications, MEDICATION_COLUMNS)
  diagnoses   <- as_table(request$diagnoses, DIAGNOSIS_COLUMNS)
  dispensings <- as_table(request$dispensings, DISPENSING_COLUMNS)
  symptoms    <- unlist(request$symptoms) %||% character()
  reference_date <- as.Date(request$reference_date)

  egfr <- estimate_egfr(request$patient, request$renal_function)
  acb  <- calculate_acb(meds, kb$acb_scores)

  findings <- c(
    indication_findings(meds),
    renal_findings(meds, egfr, kb$renal_rules),
    acb_findings(acb, meds),
    interaction_findings(meds, kb$interactions),
    disease_drug_findings(meds, diagnoses, kb$disease_drug),
    adherence_findings(meds, dispensings, reference_date),
    adverse_effect_findings(meds, symptoms, kb$side_effects)
  )
  list(egfr = egfr, acb = acb, findings = sort_findings(findings))
}
