# Enhedstest af de kliniske regler. Kør fra projektroden:
#   Rscript --vanilla tests/r/test_rules.R

suppressWarnings(suppressPackageStartupMessages(library(jsonlite)))

for (module in list.files("r/R", pattern = "\\.R$", full.names = TRUE)) {
  source(module, encoding = "UTF-8")
}
kb <- load_knowledge_base("r/data")

medications <- function(...) {
  rows <- list(...)
  records <- lapply(seq_along(rows), function(i) {
    c(list(id = paste0("med-", i), strength = "", dosage = "", indication = "Indikation"), rows[[i]])
  })
  as_table(records, MEDICATION_COLUMNS)
}

finding_ids <- function(findings) vapply(findings, function(f) f$id, character(1))

tests <- list(
  "CKD-EPI 2021 giver eGFR 38 for 78-årig kvinde med kreatinin 125" = function() {
    egfr <- estimate_egfr(list(age = 78, sex = "female"), list(creatinine_umol_l = 125))
    stopifnot(egfr$value == 38, egfr$source == "ckd_epi_2021")
  },

  "Oplyst eGFR har forrang for beregning" = function() {
    egfr <- estimate_egfr(list(age = 78, sex = "female"),
                          list(creatinine_umol_l = 125, egfr_reported = 55))
    stopifnot(egfr$value == 55, egfr$source == "reported")
  },

  "Strengeste nyreregel vælges" = function() {
    meds <- medications(list(name = "Metformin", atc = "A10BA02"))
    moderate <- renal_findings(meds, list(value = 38), kb$renal_rules)
    severe   <- renal_findings(meds, list(value = 25), kb$renal_rules)
    stopifnot(moderate[[1]]$suggested_decision == "adjust",
              severe[[1]]$suggested_decision == "stop")
  },

  "Ingen nyrefund over grænsen" = function() {
    meds <- medications(list(name = "Metformin", atc = "A10BA02"))
    stopifnot(length(renal_findings(meds, list(value = 70), kb$renal_rules)) == 0)
  },

  "Manglende eGFR giver påmindelse for renalt udskilte lægemidler" = function() {
    meds <- medications(list(name = "Metformin", atc = "A10BA02"))
    stopifnot(finding_ids(renal_findings(meds, NULL, kb$renal_rules)) == "renal:missing_egfr")
  },

  "ACB summeres og giver fund ved score >= 3" = function() {
    meds <- medications(list(name = "Amitriptylin", atc = "N06AA09"),
                        list(name = "Furosemid", atc = "C03CA01"))
    acb <- calculate_acb(meds, kb$acb_scores)
    stopifnot(acb$total == 4, length(acb_findings(acb, meds)) == 1)
  },

  "Interaktion findes uanset rækkefølge" = function() {
    meds <- medications(list(name = "Apixaban", atc = "B01AF02"),
                        list(name = "Ibuprofen", atc = "M01AE01"))
    findings <- interaction_findings(meds, kb$interactions)
    stopifnot(length(findings) == 1, findings[[1]]$severity == "high")
  },

  "Diagnosekoder normaliseres til SKS" = function() {
    stopifnot(identical(normalise_diagnosis_code(c("I50.9", "DI50.9", "dr29.6")),
                        c("DI509", "DI509", "DR296")))
  },

  "NSAID ved hjertesvigt giver diagnosefund" = function() {
    meds <- medications(list(name = "Ibuprofen", atc = "M01AE01"))
    diagnoses <- as_table(list(list(code = "I50.9", text = "Hjertesvigt")), DIAGNOSIS_COLUMNS)
    findings <- disease_drug_findings(meds, diagnoses, kb$disease_drug)
    stopifnot(finding_ids(findings) == "diagnosis:hf_nsaid:med-1")
  },

  "Lang tid siden udlevering giver adhærensfund" = function() {
    meds <- medications(list(name = "Simvastatin", atc = "C10AA01"))
    dispensings <- as_table(list(list(dispensed_on = "2026-03-01", name = "Simvastatin", atc = "C10AA01")),
                            DISPENSING_COLUMNS)
    findings <- adherence_findings(meds, dispensings, as.Date("2026-10-01"))
    stopifnot(finding_ids(findings) == "adherence:gap:med-1")
  },

  "Symptom kobles til mulige årsagspræparater" = function() {
    meds <- medications(list(name = "Amitriptylin", atc = "N06AA09"),
                        list(name = "Paracetamol", atc = "N02BE01"))
    findings <- adverse_effect_findings(meds, c(" Mundtørhed "), kb$side_effects)
    stopifnot(length(findings) == 1, unlist(findings[[1]]$medication_ids) == "med-1")
  },

  "Fund sorteres efter alvorlighed" = function() {
    findings <- list(
      new_finding("a", "renal", "low", "", "", "", "monitor"),
      new_finding("b", "renal", "high", "", "", "", "stop")
    )
    stopifnot(finding_ids(sort_findings(findings)) == c("b", "a"))
  },

  "Non-ASCII escapes giver ren ASCII" = function() {
    stopifnot(escape_non_ascii("Høj") == "H\\u00f8j")
  }
)

failures <- 0
for (name in names(tests)) {
  result <- tryCatch({ tests[[name]](); NULL }, error = function(e) conditionMessage(e))
  if (is.null(result)) {
    cat("OK    ", name, "\n")
  } else {
    failures <- failures + 1
    cat("FEJL  ", name, ":", result, "\n")
  }
}
cat(sprintf("\n%d test, %d fejl\n", length(tests), failures))
if (failures > 0) quit(status = 1)
