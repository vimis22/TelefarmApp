# ===========================================
# SETUP: Install and Load Required Packages
# ===========================================
# List of required packages
required_packages <- c("readxl", "tidyr", "fuzzyjoin", "zoo") 

# Install missing packages
install.packages(setdiff(required_packages, rownames(installed.packages())))

# Load all required packages
lapply(required_packages, library, character.only = TRUE)


# ============================================================================
# Medicinliste tab
# ============================================================================
# Use of dose_manual.xlsx
process_data <- function(rawText, ptnr) {
  tryCatch({
    today <- Sys.Date()
    
    # Read dose_manual
    doseManual <- read_xlsx("data/dose_manual.xlsx")
    doseManual <- doseManual %>%
      mutate(merged_dosis = tolower(gsub("[^A-Za-z0-9]", "", dosis))) %>%
      group_by(merged_dosis) %>%
      arrange(desc(dgl_dosis)) %>%
      slice(1) %>%
      ungroup()
    
    # Process raw text data
    data <- readLines(textConnection(rawText))
    data <- tibble(Line = data)
    start_index <- which(data$Line == "Tooltip ikoner\tUdvid/Luk") + 1
    end_index <- which(data$Line == "Lægemiddelordinationer indlæst") - 1
    relevant_data <- data[start_index:end_index, , drop = FALSE]
    group_index <- cumsum(relevant_data$Line == "Vis detaljer") + 1
    relevant_data <- relevant_data %>%
      mutate(Group = group_index) %>%
      filter(Line != "Vis detaljer") %>%
      group_by(Group) %>%
      summarize(DrugDetails = paste(Line, collapse = "\t"), .groups = 'drop')
    
    MedListFull <- relevant_data %>%
      separate(DrugDetails, into = c("Lægemiddel", "Indholdsstof", "ATC", "Styrke", "Form", "Indikation", "Remaining"), 
               sep = "\t", extra = "merge", fill = "right") %>%
      mutate(
        # Extract Dosering before Beh_Start and Beh_Slut
        Dosering = str_extract(Remaining, "^(.*?)\t(\\d{2}-\\d{2}-\\d{4}|Ukendt)"),
        Dosering = ifelse(is.na(Dosering), Remaining, str_extract(Dosering, "^[^\\t]+")),
        Beh_Start = str_extract(Remaining, "\\d{2}-\\d{2}-\\d{4}|Ukendt"),
        Beh_Slut = str_extract(Remaining, "(?<=\\d{2}-\\d{2}-\\d{4}\t)\\d{2}-\\d{2}-\\d{4}"),
        dosis = str_replace_all(tolower(Dosering), " ", ""),
        pn = 0  # Default `pn` to 0
      ) %>%
      mutate(
        # Handle Ukendt for Beh_Start
        Beh_Start = ifelse(Beh_Start == "Ukendt", NA, Beh_Start),
        Beh_Start = dmy(Beh_Start),
        Beh_Slut = dmy(Beh_Slut),
        merged_dosis = tolower(gsub("[^A-Za-z0-9]", "", Dosering))
      ) %>%
      mutate(
        # Set Beh_Start to current date if it is NA
        Beh_Start = ifelse(is.na(Beh_Start), today, Beh_Start)
      ) %>%
      filter(!str_detect(Lægemiddel, "Loading")) %>%
      mutate(Navn = paste(Lægemiddel, " (", tolower(Indholdsstof), ")", sep="")) %>%
      mutate(
        NuvBeh = ifelse(is.na(Beh_Slut) | Beh_Slut >= Sys.Date(), "Ja", "Nej")
      ) %>%
      arrange(NuvBeh) %>%
      select(-Remaining)
    
    #fuzzy_merged_data <- left_join(MedListFull, doseManual, by = "merged_dosis")
    fuzzy_merged_data <- left_join(MedListFull, doseManual, by = "merged_dosis") %>%
      mutate(
        # If a match in `doseManual`, overwrite `pn` with the matched value
        pn = as.integer(if_else(!is.na(pn.y), pn.y, pn.x, missing = pn.x))  # Use `pn` from `doseManual` if present
      ) %>%
      select(-pn.x, -pn.y)  # Clean up intermediate columns
    
    MedListSharePoint <- fuzzy_merged_data %>%
      filter(NuvBeh == "Ja") %>%
      group_by(Lægemiddel, Indholdsstof, ATC, Styrke, Form, Indikation, Dosering) %>%
      filter(Beh_Start == min(Beh_Start, na.rm = TRUE)) %>%  # Keep rows with the oldest Beh_Start
      ungroup() %>%  # Remove grouping
      
      distinct(Beh_Start, Lægemiddel, Indholdsstof, ATC, Styrke, Form, Indikation, Dosering, .keep_all = TRUE) %>%
      select(Beh_Start, Lægemiddel, Indholdsstof, ATC, Styrke, Form, Indikation, Dosering, dgl_dosis, pn)
    
    MedListSharePoint$ptnr <- ptnr
    MedListSharePoint$drugid <- 0L
    MedListSharePoint$rx_no <- seq_len(nrow(MedListSharePoint))
    MedListSharePoint$intervention <- 0L
    MedListSharePoint$followup <- 9L
    MedListSharePoint$VNR <- 0L
    
    
    MedListSharePoint <- MedListSharePoint[, c("Beh_Start", "Indholdsstof", "Lægemiddel", "ATC", "ptnr", "drugid", "rx_no", "Form", "Styrke", "Dosering", "Indikation", "intervention", "followup", "dgl_dosis", "VNR", "pn")]
    
    return(MedListSharePoint)
    
    
  }, error = function(e) {
    return(NULL)
  })
}

#===================================================================
# Diagnosis tab
# =================================================================
# Use icpc_icd10_mapping.csv and icd10.csv
# Diagnosis Info correctly categorized based on the input

# Function that collects table with columns "ICPC.kode", "ICPC.diagnose", "ICD10.kode", "ICD10.diagnose", "ICD10.tekst" 
loadDiagnosisData <- function() {
  icpcicd10 <- read.csv("data/icpc_icd10_mapping.csv", header = TRUE, sep = ";", encoding = "UTF-8")
  icpcicd10 <- icpcicd10 %>% 
    mutate(ICD10.kode = toupper(ICD10.kode)) 
  icd10 <- read.csv("data/icd10.csv", header = TRUE, sep = "\t", encoding = "UTF-8")
  icpcicd10 <- full_join(icpcicd10, icd10, by = "ICD10.kode")
}

extractDiagnoses <- function(data, icpcicd10) {
  start_index <- which(data$Line == "Journalnotat") + 1
  end_index <- grep("Viser 1.*", data$Line) - 1
  relevant_data <- data[start_index:end_index, , drop = FALSE]
  
  extract_first_date <- function(line) {
    matches <- str_match(line, "\\b(\\d{2}\\.\\d{2}\\.\\d{4})\\b")
    if (is.na(matches[1])) {
      return(NA)
    } else {
      return(matches[1])
    }
  }
  
  relevant_diagnosis_data <- relevant_data %>%
    mutate(Date = sapply(Line, extract_first_date)) %>%
    mutate(Group = cumsum(!is.na(Date) & lag(is.na(Date), default = TRUE))) %>%
    filter(Line != "\\b(\\d{2}\\.\\d{2}\\.\\d{4})\\b.*") %>%
    group_by(Group) %>%
    summarize(ForloebTekst = paste(Line, collapse = "\t"), .groups = 'drop')
  
  # Table with columns Diagnose (from input text), dato_senest, dato_startforloeb
  diagnoser <- relevant_diagnosis_data %>%
    separate(ForloebTekst, into = c("dato_senest", "dato_startforloeb", "Afsluttetforloeb", "BehSted", "Lokalisation", "Diagnose", "Remaining"), 
             sep = "\t", extra = "merge", fill = "right") %>%
    select(dato_senest, dato_startforloeb, Diagnose) %>%
    mutate(dato_senest = dmy(dato_senest)) %>%
    mutate(dato_startforloeb= dmy(dato_startforloeb)) %>%
    filter(!grepl("^(\\-|Obs)", Diagnose))  # Filter out diagnoses that starts with "-" or "Obs"
  
  # Perform merge, matching on both ICD10.diagnose and ICD10.tekst
  merged_df <- diagnoser %>%
    # Perform the first join with ICD10.diagnose
    left_join(icpcicd10, by = c("Diagnose" = "ICD10.diagnose"), relationship = "many-to-many") %>%
    # Perform the second join with ICD10.tekst
    left_join(icpcicd10, by = c("Diagnose" = "ICD10.tekst"), relationship = "many-to-many") %>%
    # Combine matches and keep the necessary columns
    mutate(
      ICPC.kode = coalesce(ICPC.kode.x, ICPC.kode.y),
      ICPC.diagnose = coalesce(ICPC.diagnose.x, ICPC.diagnose.y),
      ICD10.kode = coalesce(ICD10.kode.x, ICD10.kode.y),
      ICD10.diagnose = coalesce(ICD10.diagnose, Diagnose),  # Preserve original ICD10.diagnose or Diagnose
      ICD10.tekst = coalesce(ICD10.tekst, Diagnose)         # Preserve original ICD10.tekst or Diagnose
    ) %>%
    select(
      dato_senest, dato_startforloeb, Diagnose,
      ICPC.kode, ICD10.kode, ICPC.diagnose,
      ICD10.diagnose, ICD10.tekst  # Keep all relevant columns
    )
  
  merged_df <- merged_df %>%
    group_by(Diagnose) %>%
    filter(dato_startforloeb == min(dato_startforloeb)) %>%
    distinct(Diagnose, .keep_all = TRUE) %>%
    arrange(dato_startforloeb)
  return(merged_df)
}






# ========================================================================
# Interactions tab
# ========================================================================
# Use ListeOverGodkendteLaegemidler.csv and anticholinergic_bcpt.xlsx

# Read in the list of drugs
drugs <- read.csv2("data/ListeOverGodkendteLaegemidler.csv", header = FALSE, sep = ",") # https://laegemiddelstyrelsen.dk/da/godkendelse/godkendelse-af-medicin/lister-over-godkendte-og-afregistrerede-laegemidler/saadan-bruger-du-listen-over-godkendte-laegemidler/
drugs <- drugs[-1, ] # Remove the first row

# Update column names and replace ATC code
drugs <- drugs %>%
  select(Drugid = V1, drugname = V5, ATC = V7) %>%
  # Replace N03AX12 with N02BF01
  mutate(ATC = ifelse(ATC == "N03AX12", "N02BF01", ATC)) %>%
  mutate(ATC = ifelse(ATC == "N03AX16", "N02BF02", ATC)) %>%
  distinct(ATC, .keep_all = TRUE)

# Read in the ACB scores from the Excel sheet
acb_data <- read_excel("data/anticholinergic_bcpt.xlsx", skip = 1) %>%
  select(DKACB, ATC)
acb_data$ACB <- acb_data$DKACB

# Join the two datasets based on ATC
drug_acb <- left_join(acb_data, drugs, by = "ATC") %>%
  mutate(ACB = ifelse(is.na(ACB), 0, ACB))

# Remove rows containing NAs in both Drugid and drugname
drug_acb <- drop_na(drug_acb, Drugid, drugname)

# Function to calculate ACB score based on ATC codes
get_acb_score <- function(atc_codes) {
  acb_subset <- drug_acb[drug_acb$ATC %in% atc_codes, ]
  total_acb <- sum(acb_subset$ACB)
  return(total_acb)
}

# Function to get drug names by ACB score
get_drugs_by_acb <- function(atc_codes, score) {
  drugs_subset <- drug_acb %>%
    filter(ACB == score & ATC %in% atc_codes) %>%
    pull(drugname)
  return(drugs_subset)
}

get_drug_ids <- function(atc_codes) {
  # Filter the data to only include the ATC codes in the input
  drugs_subset <- drugs[drugs$ATC %in% atc_codes, ]
  
  # Extract the drug ids
  drug_ids <- drugs_subset$Drugid
  
  return(drug_ids)
}

# Function to generate URL for checking interactions on Laekemiddelsok
generate_laekemiddelsok_url <- function(atc_codes) {
  base_url <- "https://interaksjoner.no/results.html?PreparatNavn="
  query_params <- str_c(atc_codes, collapse = "%0D%0A")
  url <- paste0(base_url, query_params)
  return(url)
}

# Function to generate URL for checking interactions on Stockleys
generate_stockleys_url <- function(atc_codes) {
  base_url <- "https://www-new-medicinescomplete-com.proxy1-bib.sdu.dk/#/interactions/stockley?terms="
  atc_codes_url <- paste(atc_codes, collapse = ",")
  url <- paste0(base_url, atc_codes_url)
  return(url)
}

# Function to generate URL for checking interactions on Interaktionsdatabasen.dk
generate_interaktionsdatabasen_url <- function(atc_codes) {
  drug_ids <- get_drug_ids(atc_codes)
  url <- "http://interaktionsdatabasen.dk/SearchResult.aspx?pids="
  drug_ids_url <- str_c(drug_ids, collapse = ",")
  url <- str_c(url, drug_ids_url)
  return(url)
}

# Function to process the input text and extract ATC codes
# Do not think it is working
process_atc_codes <- function(data, manual_input) {
  atc_codes_from_data <- if (!is.null(data)) unique(data$ATC) else NULL
  atc_codes_from_manual_input <- manual_input %>%
    strsplit("\r?\n") %>%
    unlist() %>%
    trimws() %>%
    unique()
  
  if (length(atc_codes_from_manual_input) > 0) {
    return(atc_codes_from_manual_input)
  } else if (!is.null(atc_codes_from_data)) {
    return(atc_codes_from_data)
  } else {
    return(NULL)
  }
}

# Function to get ACB categories
get_acb_categories <- function(atc_codes) {
  list(
    category3 = get_drugs_by_acb(atc_codes, 3),
    category2 = get_drugs_by_acb(atc_codes, 2),
    category1 = get_drugs_by_acb(atc_codes, 1)
  )
}


#======================================================================
# Effektueret tab
# =====================================================================
# Use of ListeOverGodkendteLaegemidler.csv
process_effectuated_data <- function(raw_text) {
  # 1. Read data from the text area input as whole lines
  data <- readLines(textConnection(raw_text))
  
  # 2. Convert data to a tibble
  data <- tibble(Line = data)
  
  # 3. Read the lines from below "Tooltip ikoner Udvid/Luk" to one line above "Lægemiddelordinationer indlæst"
  start_index <- which(data$Line == "Metode") + 4
  end_index <- which(data$Line == "Loading") - 1
  
  # Extract the lines within the range
  DrugDetails <- data[start_index:end_index, , drop = FALSE]
  
  # 5. Split into columns, handle optional end date
  Effectuated <- DrugDetails %>%
    separate(Line, into = c("date", "drugname", "strength", "pack", "no", "Metode", "Apotek"), 
             sep = "\\t", extra = "merge", fill = "right") %>%
    select(date, drugname, strength, pack, no) %>%
    mutate(pack_numeric = as.numeric(str_extract(pack, "\\d+"))) %>%
    mutate(date = dmy(date))  %>%  # Convert date column to the desired format
    mutate(drugname = gsub(pattern = '"[^"]+"|e$', replacement = '', x = drugname),
           first_word = str_extract(drugname, "\\w+")) # extract first word of drugname
  
  # read list of approved drugs, select relevant columns, and clean drugname column
  drugs <- read.csv2("data/ListeOverGodkendteLaegemidler.csv", header = FALSE, sep =",") %>%
    select(drugname = V2, strength = V4, ATC = V7) %>%
    filter(str_length(ATC) <= 7) %>%
    distinct(drugname, strength, ATC, .keep_all = TRUE) %>%
    mutate(drugname = str_replace(drugname, pattern = '"[^"]+"|e$', replacement = '')) %>%
    mutate(first_word = str_extract(drugname, "\\w+")) # Extract first word of drugname
  
  # join data and approved drugs by first word and strength of drugname
  atcdata <- left_join(Effectuated, drugs, by = c("first_word", "strength"), relationship = "many-to-many") %>%
    rename(drugname = drugname.x) %>%
    distinct(date, drugname, strength, pack, no, ATC, pack_numeric, .keep_all = FALSE) %>% # keep unique rows
    # arrange by ATC, strength, and date
    arrange(ATC, strength, date) %>%
    
    # calculate daily consumption and format columns
    group_by(ATC, strength) %>% # group by ATC and strength
    mutate(
      no_numeric = as.numeric(no), # convert no column to numeric
      daily_consumption = round(pack_numeric * no_numeric / abs(as.numeric(difftime(date, lead(date), units = "days"))), digits = 1),
      date = format(date, "%d-%m-%Y")
    ) %>%
    ungroup() %>% # remove grouping
    mutate(
      daily_consumption_7day_avg = round(rollmean(daily_consumption, k = 7, fill = NA, align = "right"), digits = 1)) %>% # calculate rolling 7-day average of daily consumption 
    select(date, drugname, strength, pack, no, ATC, pack, no, daily_consumption, daily_consumption_7day_avg)
  
  return(atcdata)
}

#======================================================================
# Bivirkninger tab
# =====================================================================
# Use data/atc_bivirkninger_data.csv

filtered_bivirkninger_data <- function(data) {
  atc_bivirkninger_data <- read_csv("data/atc_bivirkninger_data.csv", show_col_types = FALSE)
  req(data)  # Ensure `data` exists
  
  if (nrow(data) == 0) {
    return(data.frame())  # Return an empty dataframe if no data
  }
  
  # Extract relevant columns from `data`
  data_subset <- data %>%
    select(ATC, `Lægemiddel`, `Indholdsstof`) %>%
    distinct()  # Avoid duplicates
  
  # Merge datasets based on ATC values
  result <- atc_bivirkninger_data %>%
    filter(ATC %in% data$ATC) %>%
    left_join(data_subset, by = "ATC", relationship = "many-to-many") %>%
    select(ATC, `Lægemiddel`, `Indholdsstof`, systemorganklasse, hyppighed, sværhedsgrad, bivirkning, url)
  
  return(result)
}









