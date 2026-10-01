# Nyrefunktion: eGFR-estimat og dosering af renalt udskilte lægemidler.

ckd_epi_2021 <- function(creatinine_umol_l, age, sex) {
  scr    <- creatinine_umol_l / 88.4                 # µmol/L → mg/dL
  female <- identical(sex, "female")
  kappa  <- if (female) 0.7 else 0.9
  alpha  <- if (female) -0.241 else -0.302
  ratio  <- scr / kappa
  egfr   <- 142 * min(ratio, 1)^alpha * max(ratio, 1)^-1.200 * 0.9938^age
  if (female) egfr * 1.012 else egfr
}

# Et oplyst eGFR har forrang; ellers beregnes CKD-EPI 2021 ud fra kreatinin.
estimate_egfr <- function(patient, renal_function) {
  reported <- renal_function$egfr_reported
  if (!is.null(reported)) {
    return(list(value = round(as.numeric(reported)), source = "reported"))
  }
  creatinine <- renal_function$creatinine_umol_l
  if (is.null(creatinine) || is.null(patient$age) || is.null(patient$sex)) return(NULL)
  value <- ckd_epi_2021(as.numeric(creatinine), as.numeric(patient$age), patient$sex)
  list(value = round(value), source = "ckd_epi_2021")
}

strictest_renal_rule <- function(atc, egfr_value, rules) {
  applicable <- rules[which(startsWith(atc, rules$atc_prefix) & egfr_value < rules$egfr_below), ]
  if (nrow(applicable) == 0) return(NULL)
  applicable[which.min(applicable$egfr_below), ]
}

renal_findings <- function(meds, egfr, rules) {
  if (nrow(meds) == 0) return(list())
  if (is.null(egfr)) return(missing_egfr_findings(meds, rules))

  findings <- list()
  for (i in seq_len(nrow(meds))) {
    med <- meds[i, ]
    if (is_blank(med$atc)) next
    rule <- strictest_renal_rule(med$atc, egfr$value, rules)
    if (is.null(rule)) next
    findings[[length(findings) + 1]] <- new_finding(
      id = paste0("renal:", med$id),
      category = "renal",
      severity = rule$severity,
      title = sprintf("%s ved eGFR %s", med$name, format_number(egfr$value)),
      description = sprintf(
        "eGFR %s mL/min/1,73 m² er under grænsen på %s for %s.",
        format_number(egfr$value), format_number(rule$egfr_below), rule$drug_class
      ),
      recommendation = rule$recommendation,
      decision = rule$decision,
      medication_ids = med$id
    )
  }
  findings
}

missing_egfr_findings <- function(meds, rules) {
  affected <- meds[atc_matches_any(meds$atc, rules$atc_prefix), ]
  if (nrow(affected) == 0) return(list())
  list(new_finding(
    id = "renal:missing_egfr",
    category = "renal",
    severity = "low",
    title = "Nyrefunktion ikke oplyst",
    description = sprintf(
      "%s doseres efter nyrefunktion, men hverken kreatinin eller eGFR er oplyst.",
      join_names(affected$name)
    ),
    recommendation = "Indhent aktuel kreatinin/eGFR før dosis vurderes.",
    decision = "monitor",
    medication_ids = affected$id
  ))
}
