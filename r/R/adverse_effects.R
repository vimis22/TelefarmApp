# Bivirkninger: kobler patientens symptomer til mulige årsagspræparater.

normalise_symptom <- function(x) tolower(trimws(x))

symptom_matches <- function(symptom, known) {
  known <- normalise_symptom(known)
  known == symptom | startsWith(symptom, known) | startsWith(known, symptom)
}

adverse_effect_findings <- function(meds, symptoms, side_effects) {
  symptoms <- unique(normalise_symptom(symptoms))
  symptoms <- symptoms[symptoms != ""]
  if (nrow(meds) == 0 || length(symptoms) == 0) return(list())

  findings <- list()
  for (symptom in symptoms) {
    rules <- side_effects[symptom_matches(symptom, side_effects$symptom), ]
    suspects <- meds[atc_matches_any(meds$atc, rules$atc_prefix), ]
    if (nrow(suspects) == 0) next

    causative <- vapply(rules$atc_prefix, function(p) any(startsWith(suspects$atc, p)), logical(1))
    is_serious <- any(rules$serious[causative] == "yes")
    findings[[length(findings) + 1]] <- new_finding(
      id = paste0("adverse_effect:", gsub("[^a-z0-9æøå]", "", symptom)),
      category = "adverse_effect",
      severity = if (is_serious || nrow(suspects) >= 3) "moderate" else "low",
      title = sprintf("%s kan være lægemiddelbetinget", tools::toTitleCase(symptom)),
      description = sprintf("%s er en kendt bivirkning ved %s.",
                            tools::toTitleCase(symptom), join_names(suspects$name)),
      recommendation = "Vurdér tidsmæssig sammenhæng med opstart eller dosisændring, og overvej dosisreduktion eller seponering af det mest sandsynlige præparat.",
      decision = "monitor",
      medication_ids = suspects$id
    )
  }
  findings
}
