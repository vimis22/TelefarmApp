suppressWarnings(suppressPackageStartupMessages(library(jsonlite)))

engine_dir <- function() {
  file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
}

ENGINE_DIR <- engine_dir()
for (module in list.files(file.path(ENGINE_DIR, "R"), pattern = "\\.R$", full.names = TRUE)) {
  source(module, encoding = "UTF-8")
}

main <- function() {
  request   <- read_request()
  knowledge <- load_knowledge_base(file.path(ENGINE_DIR, "data"))
  write_response(analyse_review(request, knowledge))
}

tryCatch(main(), error = function(e) {
  message(conditionMessage(e))   # havner i stderr → ClinicalEngineError i Python
  quit(status = 1)
})