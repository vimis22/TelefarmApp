# Ind- og udlæsning: JSON via stdin/stdout og vidensgrundlaget fra CSV-filer.

MEDICATION_COLUMNS <- c("id", "name", "atc", "strength", "dosage", "indication")
DIAGNOSIS_COLUMNS  <- c("code", "text")
DISPENSING_COLUMNS <- c("dispensed_on", "name", "atc", "packages")

read_request <- function(connection = file("stdin")) {
  on.exit(close(connection))
  raw <- paste(readLines(connection, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
  if (trimws(raw) == "") stop("Tom forespørgsel modtaget på stdin.")
  jsonlite::fromJSON(raw, simplifyVector = FALSE)
}

write_response <- function(response) {
  json <- jsonlite::toJSON(response, auto_unbox = TRUE, null = "null", na = "null", digits = NA)
  cat(escape_non_ascii(enc2utf8(as.character(json))))
}

# stdout på Windows bruger systemets tegnsæt (cp1252), så æ/ø/å ville blive ødelagt.
# JSON-escapes (æ) er ren ASCII og dermed uafhængige af tegnsættet.
escape_non_ascii <- function(text) {
  codes <- utf8ToInt(text)
  if (all(codes < 128)) return(text)
  chars <- intToUtf8(codes, multiple = TRUE)
  wide <- codes >= 128
  chars[wide] <- vapply(codes[wide], json_unicode_escape, character(1))
  paste(chars, collapse = "")
}

json_unicode_escape <- function(code) {
  if (code < 0x10000) return(sprintf("\\u%04x", code))
  offset <- code - 0x10000                      # tegn uden for BMP kræver surrogatpar
  sprintf("\\u%04x\\u%04x", 0xD800 + offset %/% 0x400, 0xDC00 + offset %% 0x400)
}

# Omdanner en liste af JSON-objekter til en data.frame med faste tekstkolonner.
# Manglende felter og null bliver til "" så reglerne ikke skal håndtere NULL.
as_table <- function(records, columns) {
  if (is.null(records) || length(records) == 0) {
    empty <- lapply(columns, function(x) character())
    names(empty) <- columns
    return(as.data.frame(empty, stringsAsFactors = FALSE))
  }
  rows <- lapply(records, function(record) {
    values <- lapply(columns, function(column) {
      value <- record[[column]]
      if (is.null(value) || length(value) == 0 || is.na(value[[1]])) "" else as.character(value[[1]])
    })
    names(values) <- columns
    values
  })
  as.data.frame(do.call(rbind, lapply(rows, as.data.frame, stringsAsFactors = FALSE)),
                stringsAsFactors = FALSE)
}

read_rule_table <- function(path) {
  table <- utils::read.csv(path, sep = ";", quote = "\"", stringsAsFactors = FALSE,
                           fileEncoding = "UTF-8", strip.white = TRUE, comment.char = "#")
  table[] <- lapply(table, function(column) if (is.character(column)) enc2utf8(column) else column)
  table
}

load_knowledge_base <- function(data_dir) {
  files <- c(
    renal_rules  = "renal_rules.csv",
    acb_scores   = "acb_scores.csv",
    interactions = "interactions.csv",
    disease_drug = "disease_drug.csv",
    side_effects = "side_effects.csv"
  )
  lapply(files, function(file) read_rule_table(file.path(data_dir, file)))
}
