# Lægemiddelinteraktioner mellem to præparater på medicinlisten.

pair_matches <- function(atc_x, atc_y, rule) {
  (startsWith(atc_x, rule$atc_a) && startsWith(atc_y, rule$atc_b)) ||
    (startsWith(atc_x, rule$atc_b) && startsWith(atc_y, rule$atc_a))
}

interaction_findings <- function(meds, interactions) {
  n <- nrow(meds)
  if (n < 2 || nrow(interactions) == 0) return(list())

  findings <- list()
  for (i in seq_len(n - 1)) {
    for (j in (i + 1):n) {
      if (is_blank(meds$atc[i]) || is_blank(meds$atc[j])) next
      for (r in seq_len(nrow(interactions))) {
        rule <- interactions[r, ]
        if (!pair_matches(meds$atc[i], meds$atc[j], rule)) next
        findings[[length(findings) + 1]] <- new_finding(
          id = sprintf("interaction:%s:%s:%s", rule$rule_id, meds$id[i], meds$id[j]),
          category = "interaction",
          severity = rule$severity,
          title = sprintf("%s + %s", meds$name[i], meds$name[j]),
          description = sprintf("%s: %s", rule$title, rule$description),
          recommendation = rule$recommendation,
          decision = rule$decision,
          medication_ids = c(meds$id[i], meds$id[j])
        )
      }
    }
  }
  findings
}
