# Lægemidler der er uhensigtsmæssige ved patientens diagnoser.

# Ensretter til SKS-format: "I50.9" → "DI509", "DI50.9" → "DI509".
normalise_diagnosis_code <- function(code) {
  code <- gsub("[^A-Z0-9]", "", toupper(code))
  ifelse(grepl("^D[A-Z]", code) | code == "", code, paste0("D", code))
}

disease_drug_findings <- function(meds, diagnoses, rules) {
  if (nrow(meds) == 0 || nrow(diagnoses) == 0) return(list())
  codes <- normalise_diagnosis_code(diagnoses$code)

  findings <- list()
  for (r in seq_len(nrow(rules))) {
    rule <- rules[r, ]
    diagnosis_hit <- which(startsWith(codes, rule$diagnosis_prefix))
    if (length(diagnosis_hit) == 0) next
    affected <- meds[atc_matches_any(meds$atc, rule$atc_prefix), ]
    if (nrow(affected) == 0) next
    diagnosis_text <- diagnoses$text[diagnosis_hit[1]]

    for (i in seq_len(nrow(affected))) {
      findings[[length(findings) + 1]] <- new_finding(
        id = sprintf("diagnosis:%s:%s", rule$rule_id, affected$id[i]),
        category = "diagnosis",
        severity = rule$severity,
        title = sprintf("%s ved %s", affected$name[i], tolower(diagnosis_text)),
        description = rule$description,
        recommendation = rule$recommendation,
        decision = rule$decision,
        medication_ids = affected$id[i]
      )
    }
  }
  findings
}
