# Adhærens: sammenholder medicinlisten med apoteksudleveringer.

ADHERENCE_LOOKBACK_DAYS <- 365   # periode der vurderes
ADHERENCE_GAP_DAYS      <- 120   # længere tid uden udlevering tyder på ophold
UNLISTED_RECENT_DAYS    <- 180   # udleveringer uden ordination i denne periode

first_word <- function(x) tolower(sub("[[:space:]].*$", "", trimws(x)))

dispensings_for <- function(med, dispensings) {
  same_atc  <- !is_blank(med$atc) & dispensings$atc == med$atc
  same_name <- first_word(dispensings$name) == first_word(med$name)
  dispensings[same_atc | same_name, ]
}

adherence_findings <- function(meds, dispensings, reference_date) {
  if (nrow(meds) == 0 || nrow(dispensings) == 0) return(list())
  dispensings$date <- as.Date(dispensings$dispensed_on)
  dispensings <- dispensings[!is.na(dispensings$date) &
                               dispensings$date >= reference_date - ADHERENCE_LOOKBACK_DAYS, ]

  findings <- list()
  for (i in seq_len(nrow(meds))) {
    finding <- medication_adherence_finding(meds[i, ], dispensings, reference_date)
    if (!is.null(finding)) findings[[length(findings) + 1]] <- finding
  }
  c(findings, unlisted_dispensing_findings(meds, dispensings, reference_date))
}

medication_adherence_finding <- function(med, dispensings, reference_date) {
  matched <- dispensings_for(med, dispensings)
  if (nrow(matched) == 0) {
    return(new_finding(
      id = paste0("adherence:none:", med$id),
      category = "adherence",
      severity = "moderate",
      title = sprintf("%s er ikke udleveret", med$name),
      description = sprintf("Ingen apoteksudlevering af %s inden for de seneste %d dage.",
                            medication_label(med), ADHERENCE_LOOKBACK_DAYS),
      recommendation = "Afklar om præparatet tages. Overvej seponering hvis det ikke anvendes.",
      decision = "undecided",
      medication_ids = med$id
    ))
  }
  last_date <- max(matched$date)
  days_since <- as.integer(reference_date - last_date)
  if (days_since <= ADHERENCE_GAP_DAYS) return(NULL)

  new_finding(
    id = paste0("adherence:gap:", med$id),
    category = "adherence",
    severity = "moderate",
    title = sprintf("Mulig manglende adhærens: %s", med$name),
    description = sprintf("Seneste udlevering var %s (%d dage siden).",
                          format(last_date, "%d-%m-%Y"), days_since),
    recommendation = "Drøft adhærens med patienten og afklar om behandlingen fortsat er relevant.",
    decision = "monitor",
    medication_ids = med$id
  )
}

unlisted_dispensing_findings <- function(meds, dispensings, reference_date) {
  recent <- dispensings[dispensings$date >= reference_date - UNLISTED_RECENT_DAYS, ]
  if (nrow(recent) == 0) return(list())

  listed_atc  <- meds$atc[!vapply(meds$atc, is_blank, logical(1))]
  listed_name <- first_word(meds$name)
  unlisted <- recent[!(recent$atc %in% listed_atc) & !(first_word(recent$name) %in% listed_name), ]
  if (nrow(unlisted) == 0) return(list())

  lapply(unique(unlisted$name), function(name) {
    rows <- unlisted[unlisted$name == name, ]
    new_finding(
      id = paste0("adherence:unlisted:", gsub("[^a-z0-9]", "", tolower(name))),
      category = "adherence",
      severity = "low",
      title = sprintf("%s udleveret, men ikke på medicinlisten", name),
      description = sprintf("Seneste udlevering %s. Præparatet findes ikke blandt de aktuelle ordinationer.",
                            format(max(rows$date), "%d-%m-%Y")),
      recommendation = "Afklar om patienten tager præparatet, og opdatér FMK.",
      decision = "undecided"
    )
  })
}
