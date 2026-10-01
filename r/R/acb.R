# Antikolinerg byrde (Anticholinergic Cognitive Burden, ACB).

ACB_CLINICALLY_RELEVANT <- 3

acb_score_for <- function(atc, acb_scores) {
  if (is_blank(atc)) return(0L)
  matches <- acb_scores[startsWith(atc, acb_scores$atc), ]
  if (nrow(matches) == 0) return(0L)
  as.integer(max(matches$score))
}

calculate_acb <- function(meds, acb_scores) {
  items <- list()
  for (i in seq_len(nrow(meds))) {
    score <- acb_score_for(meds$atc[i], acb_scores)
    if (score > 0) items[[length(items) + 1]] <- list(medication_id = meds$id[i], score = score)
  }
  total <- sum(vapply(items, function(item) item$score, integer(1)))
  list(total = total, items = items)
}

acb_findings <- function(acb, meds) {
  if (acb$total < ACB_CLINICALLY_RELEVANT) return(list())

  ids    <- vapply(acb$items, function(item) item$medication_id, character(1))
  scores <- vapply(acb$items, function(item) item$score, integer(1))
  names_by_id <- setNames(meds$name, meds$id)
  strongest <- names_by_id[ids[scores == max(scores)]]

  list(new_finding(
    id = "acb:total",
    category = "acb",
    severity = if (acb$total >= 5) "high" else "moderate",
    title = sprintf("Høj antikolinerg byrde (ACB %d)", acb$total),
    description = sprintf(
      "Samlet ACB-score %d fordelt på %s. En score på 3 eller mere er forbundet med kognitiv svækkelse, fald og øget mortalitet hos ældre.",
      acb$total, join_names(names_by_id[ids])
    ),
    recommendation = sprintf("Overvej at seponere eller erstatte %s med et mindre antikolinergt alternativ.",
                             join_names(strongest)),
    decision = "adjust",
    medication_ids = ids[scores == max(scores)]   # forslaget gælder kun de stærkest antikolinerge
  ))
}
