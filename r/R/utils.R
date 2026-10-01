# Fælles hjælpefunktioner for regelmodulerne.

SEVERITIES <- c("high", "moderate", "low")
DECISIONS  <- c("undecided", "continue", "adjust", "stop", "monitor")
CATEGORIES <- c("indication", "renal", "acb", "interaction", "diagnosis", "adherence", "adverse_effect")

# Opretter et fund i det format, som Python-laget forventer (se JSON-kontrakten).
new_finding <- function(id, category, severity, title, description, recommendation,
                        decision, medication_ids = character()) {
  stopifnot(
    category %in% CATEGORIES,
    severity %in% SEVERITIES,
    decision %in% DECISIONS
  )
  list(
    id = id,
    category = category,
    severity = severity,
    title = title,
    description = description,
    recommendation = recommendation,
    suggested_decision = decision,
    medication_ids = as.list(unname(medication_ids))
  )
}

severity_rank <- function(severity) match(severity, SEVERITIES)

sort_findings <- function(findings) {
  if (length(findings) == 0) return(list())
  ranks <- vapply(findings, function(f) severity_rank(f$severity), integer(1))
  findings[order(ranks)]
}

is_blank <- function(x) is.null(x) || length(x) == 0 || is.na(x[1]) || trimws(x[1]) == ""

# TRUE for hver ATC-kode i `atc`, der starter med et af `prefixes`.
atc_matches_any <- function(atc, prefixes) {
  if (length(prefixes) == 0) return(rep(FALSE, length(atc)))
  vapply(atc, function(code) {
    !is_blank(code) && any(startsWith(code, prefixes))
  }, logical(1), USE.NAMES = FALSE)
}

medication_label <- function(med_row) {
  label <- trimws(paste(med_row$name, med_row$strength))
  if (label == "") med_row$atc else label
}

join_names <- function(names) {
  names <- unique(names)
  if (length(names) <= 1) return(paste(names, collapse = ""))
  paste(paste(names[-length(names)], collapse = ", "), "og", names[length(names)])
}

format_number <- function(x) format(round(x), big.mark = ".", decimal.mark = ",")
