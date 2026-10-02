# ===========================================
# SETUP: Install and Load Required Packages
# ===========================================
# List of required packages
required_packages <- c("shiny", "DT", "tidyverse", "readr", "zoo", "shinyjs", "lubridate", "rhandsontable") 

# Install missing packages
install.packages(setdiff(required_packages, rownames(installed.packages()))) 

# Load all required packages
lapply(required_packages, library, character.only = TRUE)


# ====================================
# CONFIGURATION: General Settings
# ====================================
# Uncomment the line below and run it separately if UTF-8 encoding issues occur:
# Sys.setlocale("LC_ALL", "en_US.UTF-8") 

# Remove this line below if you want the app to run directly in Rstudio instead of in the browser (Copy buttons might not work in the Rstudio interface)
options(shiny.launch.browser = TRUE)

directory <-  "Z:/Doc/TFA/Telefarmakologisk_Ambulatorium_App" 
setwd(directory) 

# Source external R scripts
source("source/source.R")

# ===========================================
# DEFINE USER INTERFACE (UI)
# ===========================================
ui <- fluidPage(
  useShinyjs(),  # Enable shinyjs for toggling UI elements
  titlePanel("Medicingennemgangværktøj, Farmakologi OUH"),
  
  # Styling configuration for DataTables
  tags$head(
    tags$style(HTML("
    /* DataTables styling */
    .dataTables_wrapper .dataTables_info, 
    .dataTables_wrapper .dataTables_paginate .paginate_button,
    .dataTables_wrapper .dataTables_filter input,
    .dataTables_wrapper .dataTables_length select,
    table.dataTable {
      font-size: 12px;
    }
    /* Styling for verbatimTextOutput to wrap text */
    .shiny-text-output {
      white-space: pre-wrap; /* Preserves newlines and wraps text */
      word-wrap: normal; /* Prevents breaking words */
      overflow-wrap: normal; /* Ensures whole words remain intact */
    }
    
  "))
  ),
  
  tabsetPanel(
    # Input tab
    tabPanel("Input",
             fluidRow(
               # First column
               column(width = 6,
                      wellPanel(
                        # Patientnummer input
                        numericInput("ptnr", "Patientnummer:", value = NULL,  min = 0),
                        div(id = "ptnr_warning", style = "color: red; display: none;",
                            "Patientnummer skal udfyldes før andre funktionaliteter bliver tilgængelige."),
                        # FMK Aktuelle ordinationer input
                        textAreaInput("rawText", "Aktuelle ordinationer (FMK)", "", rows = 10, cols = 50)
                      )
               ),
               # Second column
               column(width = 6,
                      wellPanel(
                        # Diagnoser - Sundhedsjournalen input
                        textAreaInput("diagnosesInput", "Diagnoser (Sundhedsjournalen)", "", rows = 10, cols = 50),
                        # FMK Apoteksudleveringer input
                        textAreaInput("effectuatedRawText", "Apoteksudleveringer (FMK)", "", rows = 10, cols = 50),
                        div(id = "effectuated_warning", style = "color: red; display: none;",
                            "Udfyld venligst Aktuelle ordinationer før du udfylder Apoteksudleveringer."),
                        # eGFR input
                        numericInput("eGFR", "eGFR (mL/min/1.73 m²):", value = 60, min = 0)
                      )
               )
             ),
             mainPanel(
               p("Indsæt patientdata i tektsfelterne og skift mellem fanerne for at se relevant data.")
             )
    ),
    # Medicinliste tab
    tabPanel("Medicinliste",
             # Medicinliste Tekst at the top
             uiOutput("Medicinliste_tekst"),
             
             # Buttons below the text
             div(
               tags$button(
                 id = "copy_table_no_header_btn",
                 class = "btn btn-warning",
                 "Kopier Tabel Uden Kolonnenavne",
                 style = "margin-bottom: 10px; margin-left: 10px;"
               ),
               tags$button(
                 id = "copy_lægemiddel_btn",
                 class = "btn btn-primary", 
                 "Kopier Lægemiddelliste",
                 style = "margin-bottom: 10px; margin-left: 10px;"
               ),
               style = "margin-bottom: 20px;"  # Spacing below the buttons
             ),
             
             # Table below the buttons
             rHandsontableOutput("drugTable"), 
             tags$script(HTML("
        
  // Copy Table Without Header
  document.getElementById('copy_table_no_header_btn').addEventListener('click', function() {
    const table = document.querySelector('.handsontable table'); // Select the rhandsontable
    if (table) {
      let text = '';
      const rows = table.querySelectorAll('tr');
      rows.forEach((row, index) => {
        if (index > 0) { // Skip the header row
          const cols = row.querySelectorAll('td');
          const rowText = Array.from(cols).map(col => 
            col.innerText.replace(/\\n/g, ' ') // Replace newlines within cells with space
          ).join('\\t'); // Tab-delimited
          text += rowText + '\\n'; // Newline after each row
        }
      });
      // Copy to clipboard
      navigator.clipboard.writeText(text).then(() => {
        alert('Table copied to clipboard without header!');
      }).catch(err => {
        alert('Failed to copy table: ' + err);
      });
    } else {
      alert('Table not found!');
    }
  });

  // Copy only distinct 'Lægemiddel' column values without header
  document.getElementById('copy_lægemiddel_btn').addEventListener('click', function() {
    const table = document.querySelector('.handsontable table'); // Select the rhandsontable
    if (table) {
      const distinctValues = new Set(); // Use a Set to store unique values
      const rows = table.querySelectorAll('tr');
      rows.forEach((row, index) => {
        if (index > 0) { // Skip the header row
          const cols = row.querySelectorAll('td'); // Get table data cells only
          if (cols.length > 0) {
            const lægemiddelCol = cols[1]; // Adjust index if needed
            if (lægemiddelCol) {
              distinctValues.add(lægemiddelCol.innerText.trim()); // Add unique value to the Set
            }
          }
        }
      });
      // Convert the Set to a string for copying
      const text = Array.from(distinctValues).join('\\n'); // Join values with newlines
      // Copy to clipboard
      navigator.clipboard.writeText(text).then(() => {
        alert('Lægemiddel column copied to clipboard without header!');
      }).catch(err => {
        alert('Failed to copy Lægemiddel column: ' + err);
      });
    } else {
      alert('Table not found!');
    }
  });

  
  "))
    ),
    # Diagnoser tab
    tabPanel("Diagnoser",
             sidebarLayout(
               # Checkbox with diagnoser
               sidebarPanel(
                 checkboxGroupInput("selectedDiagnoses", "Vælg Diagnoser")),
               # Output with "diagnoseTable" and additional text
               mainPanel(
                 uiOutput("Diagnose_tekst"),
                 rHandsontableOutput("diagnoseTable"),
                 # Show text output
                 checkboxInput("show_without_diag", "Fravælg visning af ICPC teksten", value = FALSE), 
                 verbatimTextOutput("generatedText")
               )
             )
    ),
    # Interaktioner tab
    tabPanel("Interaktioner",
             sidebarLayout(
               sidebarPanel(
                 actionButton("check_interactions_dk", "Interaktionsdatabasen", class = "btn-primary"),
                 actionButton("check_interactions_uk", "Stockleys", class = "btn-primary"),
                 actionButton("check_interactions_no", "Interaksjoner", class = "btn-primary"),
                 textAreaInput("manualAtc", "ATC koder til interaktions/ACB søgning", "", rows = 10, cols = 50),
                 p("Hvis du ikke har FMK medicinlisten men kun ATC koderne, kan de indsættes i tekstfeltet")
               ),
               mainPanel(
                 h3("Antikolinerg belastnings score:"),
                 verbatimTextOutput("acb_output"),
                 h3("Kategorier for antikolinerg belastning:"),
                 h4("Kategori 3 - meget stærk effekt:"), verbatimTextOutput("acb_cat3_output"),
                 h4("Kategori 2 - stærk effekt:"), verbatimTextOutput("acb_cat2_output"),
                 h4("Kategori 1 - lille-moderat effekt:"), verbatimTextOutput("acb_cat1_output")
               )
             )
    ),
    # Effektueret tab
    tabPanel("Effektueret",
             # Show the "effectuatedTable" table
             fluidRow(column(width = 12, 
                             # Dynamically render the dropdown filter
                             uiOutput("filter_pn"),
                             DTOutput("effectuatedTable")))
    ),
    # Nyrefunktion tab
    tabPanel(
      "Nyrefunktion",
      fluidRow(
        # First column
        # Place the checkbox above the recommendations
        column(width = 9,
               checkboxInput("show_all_renal", "Vis information om nedsat nyrefunktion for alle GFR værdier", value = FALSE),
               # Render renal recommendations below the checkbox
               uiOutput("renal_recommendations") 
        ),
        # Second column
        column(width = 3,
               uiOutput("links_kidney_drugs")  # Warnings and links
        )
      )
    ),
    
    # Bivirkninger tab
    tabPanel(
      "Bivirkninger",
      fluidRow(
        # First column
        column(width = 9,
               uiOutput("Bivirkninger_tekst"),
               DTOutput("bivirkninger_list"),
               uiOutput("generatedTextBivirkninger"),
               
               # JavaScript to capture checked rows
               tags$script(HTML("
                $(document).on('change', 'input[name=selectRow]', function() {
                  var selected = [];
                  $('input[name=selectRow]:checked').each(function() {
                    selected.push($(this).val());
                  });
                  Shiny.setInputValue('selected_checkbox_rows', selected);
                });
              "))
        ),
        # Second column
        column(width = 3,
               uiOutput("links_side_effects_drugs")  # Warnings and links
        )
      )
    )
    
  )
)

# ===========================================
# SERVER LOGIC
# ===========================================

server <- function(input, output, session) {
  ################# Global reactive values #########################
  # Store app-wide reactive values for dynamic updates
  values <- reactiveValues(
    data = NULL,
    atc_codes = NULL,
    drug_names = NULL,
    selectedDiagnosesData = NULL,
    selectedDiagnoses = NULL,
    editedData = NULL
  )
  # Store imported diagnoses as a reactive value
  importedDiagnoser <- reactiveVal(NULL)
  
  
  
  
  ################## # Input tab functionality #######################
  # Check if Patientnummer is filled
  observe({
    patient_filled <- !is.null(input$ptnr) && input$ptnr >= 0
    
    # Enable or disable other input fields
    shinyjs::toggleState("rawText", condition = patient_filled)
    shinyjs::toggleState("diagnosesInput", condition = patient_filled)
    shinyjs::toggleState("effectuatedRawText", condition = patient_filled)
    shinyjs::toggleState("eGFR", condition = patient_filled)
    
    # Show or hide warning message
    shinyjs::toggle(id = "ptnr_warning", condition = !patient_filled)
  })
  
  
  # Process raw text input into a data table
  observe({
    if (input$rawText != "") {
      values$data <- process_data(input$rawText, input$ptnr)
    } else {
      values$data <- NULL
    }
  })
  
  # Lock or unlock `effectuatedRawText` and show warning
  observe({
    patient_filled <- !is.null(input$ptnr) && input$ptnr >= 0
    raw_text_filled <- input$rawText != ""
    
    # Enable `effectuatedRawText` only if `patient_filled` and `rawText` are satisfied
    shinyjs::toggleState("effectuatedRawText", condition = patient_filled && raw_text_filled)
    
    # Show warning if `rawText` is empty
    shinyjs::toggle(id = "effectuated_warning", condition = !raw_text_filled)
  })
  
  
  # Process diagnoses input and update choices
  observe({
    if (input$diagnosesInput != "") {
      data <- tibble(Line = unlist(strsplit(input$diagnosesInput, "\n")))
      icpcicd10 <- loadDiagnosisData()
      importedDiagnoser(extractDiagnoses(data, icpcicd10))
      updateCheckboxGroupInput(
        session, "selectedDiagnoses", 
        choices = setNames(
          importedDiagnoser()$Diagnose,
          paste(importedDiagnoser()$Diagnose, "(", format(importedDiagnoser()$dato_startforloeb, "%Y"), ")")))
    }
  })
  
  # 
  selectedDiagnoses <- reactive({
    input$selectedDiagnoses
  })
  
  
  ################### Medicinliste tab functionality #########################
  
  # Render the rhandsontable
  output$drugTable <- renderRHandsontable({
    if (!is.null(values$data)) {
      # Create a subset of the data for display (exclude "Beh_Start")
      display_data <- values$data %>%
        select(-`Beh_Start`, -`Indholdsstof (Lægemiddel)`) %>%
        mutate(across(everything(), ~ ifelse(is.na(.) | is.null(.), " ", .)))  # Handle NA and NULL
      
      rhandsontable(display_data, rowHeaders = NULL, useTypes = TRUE, stretchH = "all") %>%
        hot_cols(colWidths = "auto", manualColumnResize = TRUE, columnSorting = TRUE) %>%
        hot_col("Indholdsstof", type = "text", width = 80) %>%
        hot_col("Lægemiddel", type = "text", width = 80) %>%
        hot_col("ATC", type = "text", width = 30) %>%
        hot_col("ptnr", type = "numeric", width = 30) %>%
        hot_col("drugid", type = "numeric", width = 30) %>%
        hot_col("rx_no", type = "numeric", width = 30) %>%
        hot_col("Form", type = "text", width = 90) %>%
        hot_col("Styrke", type = "text", width = 50) %>%
        hot_col("Dosering", type = "text", width = 100) %>%
        hot_col("Indikation", type = "text", width = 100) %>%
        hot_col("intervention", type = "numeric", width = 35) %>%
        hot_col("followup", type = "numeric", width = 30) %>%
        hot_col("dgl_dosis", type = "numeric", width = 30) %>%
        hot_col("VNR", type = "numeric", width = 20) %>%
        hot_col("pn", type = "numeric", width = 20)
    } 
  })
  
  # Observe changes and update the full data, preserving hidden columns
  observeEvent(input$drugTable, {
    if (!is.null(input$drugTable)) {
      # Convert rhandsontable input back to R data frame
      updated_display_data <- hot_to_r(input$drugTable)
      
      # Update only the visible columns in the original dataset
      visible_columns <- colnames(updated_display_data)
      values$data[visible_columns] <- updated_display_data  # Map edited columns back to `values$data`
    }
  })
  
  
  # Additional information to display
  output$Medicinliste_tekst <- renderUI({
    # Combine and render
    tagList(
      tags$h4("Vær opmærksom på:"),  # Headline
      tags$div(
        style = "white-space: pre-wrap;",  # Ensure line breaks
        "- pn sættes til 0 som default, hvis information om pn ikke fremgår fra dose_manual.xlsx dokumentet. Tjek derfor listen efter for eventuelle fejl."  # Message
      )
    )
  })
  
  
  
  
  ################ Diagnoser tab functionality ###########################
  # Additional information to display
  output$Diagnose_tekst <- renderUI({
    # Combine and render
    tagList(
      tags$div(tags$b("Tilføj ekstra diagnose:")), 
      tags$div(
        style = "white-space: pre-wrap;",  # Ensure line breaks
        "Vælg en diagnose til venstre så tabellen fremkommer. Højreklik på en række og vælg 'Insert row below/above'. Skriv derefter diagnosen mm. ind i felterne."
      ),
      tags$br()  # Add an empty line after the text
    )
  })
  
  # Store the diagnosis table so it persists across updates
  values <- reactiveValues(diagnoseData = NULL)
  
  # Reactive function that updates when new diagnoses are selected
  filteredDiagnosesData <- reactive({
    selected <- selectedDiagnoses()
    
    if (!is.null(selected) && length(selected) > 0) {
      new_data <- importedDiagnoser() %>%
        filter(Diagnose %in% selected) %>%
        mutate(
          dato_senest = as.character(dato_senest),
          dato_startforloeb = as.character(dato_startforloeb)
        )
      
      # Merge new selection with existing data (avoiding duplicates)
      if (!is.null(values$diagnoseData)) {
        updated_data <- bind_rows(values$diagnoseData, new_data) %>% # Does not check if diagnosis have been removed
          distinct(Diagnose, .keep_all = TRUE)  # Keep only unique diagnoses
      } else {
        updated_data <- new_data
      }
      
      return(updated_data)
    } else {
      return(NULL)  # Return NULL if no diagnoses are selected
    }
  })
  
  # Remove deselected diagnoses but keep manually added rows (Keep: Selected diagnoses, Diagnoses that do not exist in the selectable list, Manually added rows (Diagnose == NA))
  removeDeselectedDiagnoses <- reactive({
    selected <- selectedDiagnoses()  # Get current selections
    all_possible_diagnoses <- importedDiagnoser()$Diagnose  # Get ALL selectable diagnoses
    
    if (!is.null(values$diagnoseData)) {
      values$diagnoseData <- values$diagnoseData %>%
        filter(Diagnose %in% selected | !Diagnose %in% all_possible_diagnoses | is.na(Diagnose))  
    }
  })
  
  # Trigger row removal when diagnoses are deselected
  observeEvent(selectedDiagnoses(), {
    removeDeselectedDiagnoses()
  })
  
  
  # Update values$diagnoseData when a new row is added manually
  observeEvent(input$diagnoseTable, {
    if (!is.null(input$diagnoseTable)) {
      new_data <- hot_to_r(input$diagnoseTable)
      values$diagnoseData <- new_data  # Store manually added rows
    }
  })
  
  
  output$diagnoseTable <- renderRHandsontable({
    data <- filteredDiagnosesData()
    
    if (!is.null(data) && nrow(data) > 0) {
      
      # Convert 'dato_senest' to Date for sorting, then back to character
      data <- data %>%
        mutate(
          dato_senest = na_if(dato_senest, ""),  # Convert "" to NA
          date_sort = as.Date(dato_senest, format = "%Y-%m-%d")  # Convert to Date
        ) %>%
        arrange(is.na(date_sort), date_sort) %>%  # Sort: NAs last
        mutate(
          dato_senest = ifelse(is.na(dato_senest), "", dato_senest)  # Convert NA back to ""
        ) %>%
        select(-date_sort)  # Remove helper column
      
      rhandsontable(data,
                    rowHeaders = NULL,
                    selectCallback = TRUE,
                    editable = TRUE,
                    useTypes = FALSE,
                    stretchH = "all") %>%
        hot_context_menu(allowRowEdit = TRUE) %>%
        hot_cols(colWidths = "auto",  # Dynamically adjust column widths
                 manualColumnResize = TRUE,
                 columnSorting = TRUE) %>%
        hot_table(stretchH = "all",  # Ensure it stretches across the full width
                  overflow = "hidden", # Prevent horizontal scrolling
                  manualRowMove = TRUE)  # Enable manual row reordering 
    }
  })
  
  
  # Render generated text for selected diagnoses
  generatedText <- reactive({
    data <- filteredDiagnosesData()
    if (!is.null(data)) {
      # If checkbox is clicked
      if (input$show_without_diag){
        texts <- apply(data, 1, function(row) {
          paste0(
            ifelse(!is.na(row["ICD10.tekst"]) & row["ICD10.tekst"] != "", row["ICD10.tekst"], row["Diagnose"]),
            " (", format(as.Date(row["dato_startforloeb"]), "%Y"), ")\n",
            "-Nuværende:\n",
            "-Tidligere:"
          )
        })
      }
      else {
        texts <- apply(data, 1, function(row) {
          paste0(
            ifelse(!is.na(row["ICD10.tekst"]) & row["ICD10.tekst"] != "", row["ICD10.tekst"], row["Diagnose"]),
            " (", format(as.Date(row["dato_startforloeb"]), "%Y"), ")(ICPC: ", row["ICPC.kode"], ", aktuel)\n",
            "-Nuværende:\n",
            "-Tidligere:"
          )
        })
      }
      paste(texts, collapse = "\n\n")
    } else {
      "No data available."
    }
  })
  
  output$generatedText <- renderText({
    generatedText()
  })
  
  #################### Interaktioner tab functionality #######################
  # Observe changes to data and compute ACB scores
  observe({
    if (!is.null(values$data)) {
      if ("ATC" %in% colnames(values$data) && all(c("Indholdsstof", "Lægemiddel") %in% colnames(values$data))) {
        values$data <- values$data %>%
          mutate(`Indholdsstof (Lægemiddel)` = paste(Indholdsstof, Lægemiddel, sep = " - "))
        values$drug_names <- setNames(values$data$`Indholdsstof (Lægemiddel)`, values$data$ATC)
        values$atc_codes <- unique(values$data$ATC)
      } else {
        print("Expected columns not found in MedListSharePoint data")
      }
    }
    
    # Compute and display ACB scores and categories if ATC codes are available
    if (!is.null(values$atc_codes) && length(values$atc_codes) > 0) {
      acb_score <- get_acb_score(values$atc_codes)
      output$acb_output <- renderText(paste(acb_score))
      acb_categories <- get_acb_categories(values$atc_codes)
      output$acb_cat3_output <- renderPrint({ cat(paste(acb_categories$category3, collapse = "\n")) })
      output$acb_cat2_output <- renderPrint({ cat(paste(acb_categories$category2, collapse = "\n")) })
      output$acb_cat1_output <- renderPrint({ cat(paste(acb_categories$category1, collapse = "\n")) })
    } else {
      # Fallback if no ATC codes are provided
      output$acb_output <- renderText("No ATC codes provided.")
      output$acb_cat3_output <- renderPrint("")
      output$acb_cat2_output <- renderPrint("")
      output$acb_cat1_output <- renderPrint("")
    }
  })
  
  # Check interactions for ATC codes
  observeEvent(input$check_interactions_dk, {
    atc_codes <- values$atc_codes
    if (length(atc_codes) == 0) {
      showModal(modalDialog("No ATC codes available. Please check the 'Medicinliste' tab or enter them manually in the 'Input' tab."))
      return(NULL)
    }
    url <- generate_interaktionsdatabasen_url(atc_codes)
    browseURL(url)
  })
  
  observeEvent(input$check_interactions_uk, {
    atc_codes <- values$atc_codes
    if (length(atc_codes) == 0) {
      showModal(modalDialog("No ATC codes available. Please check the 'Medicinliste' tab or enter them manually in the 'Input' tab."))
      return(NULL)
    }
    url <- generate_stockleys_url(atc_codes)
    browseURL(url)
  })
  
  observeEvent(input$check_interactions_no, {
    atc_codes <- values$atc_codes
    if (length(atc_codes) == 0) {
      showModal(modalDialog("No ATC codes available. Please check the 'Medicinliste' tab or enter them manually in the 'Input' tab."))
      return(NULL)
    }
    url <- generate_laekemiddelsok_url(atc_codes)
    browseURL(url)
  })
  
  
  
  #################### Effektueret tab functionality #######################
  # Render the effectuated table
  observe({
    if (input$effectuatedRawText != "") {
      # Process the raw effectuation data
      effectuation_data <- process_effectuated_data(input$effectuatedRawText)
      
      # Add dgl_dosis and pn columns by matching on ATC, strength, and ensuring date >= Beh_Start
      effectuation_data <- effectuation_data %>%
        # Perform a join with values$data
        left_join(
          values$data %>%
            select(Beh_Start, ATC, Styrke, dgl_dosis, pn),
          by = c("ATC" = "ATC", "strength" = "Styrke"),
          relationship = "many-to-many"
        )  %>%
        mutate(
          date = as.Date(date, format = "%d-%m-%Y"),       # Convert `date` to Date type
          Beh_Start = as.Date(Beh_Start, format = "%Y-%m-%d"), # Convert `Beh_Start` to Date type
          # Calculate the difference in days
          date_diff = if_else(
            !is.na(Beh_Start),
            time_length(interval(Beh_Start, date), unit = "days"),
            Inf
          )
        ) %>%
        group_by(date, ATC, strength) %>%
        mutate(
          keep_row = case_when(
            # If all `date_diff` values are NA or negative, keep the first row
            all(is.na(date_diff) | date_diff < 0) ~ row_number() == 1,
            # If there are valid non-negative `date_diff` values, keep the row with the smallest positive value
            any(date_diff >= 0 & !is.na(date_diff)) ~ {
              valid_diff <- date_diff[date_diff >= 0 & !is.na(date_diff)]
              date_diff == if_else(length(valid_diff) > 0, suppressWarnings(min(valid_diff, na.rm = TRUE)), Inf)
            },
            # Default case for all other rows
            TRUE ~ FALSE
          ),
          dgl_dosis = case_when(
            all(date_diff < 0) ~ "",  # If all `date_diff` values are negative, clear `dgl_dosis`
            TRUE ~ as.character(dgl_dosis)  # Otherwise, keep the original value
          ),
          pn = case_when(
            all(date_diff < 0) ~ "",  # If all `date_diff` values are negative, clear `pn`
            TRUE ~ as.character(pn)  # Otherwise, keep the original value
          )
        ) %>%
        filter(keep_row) %>%  # Keep only the rows that satisfy the conditions
        ungroup() %>%
        select(-date_diff, -keep_row)  # Remove temporary columns
      
      
      
      # Add a UI element to select filter criteria for `pn`
      output$filter_pn <- renderUI({
        req(effectuation_data)  # Ensure data is loaded
        
        # Explicitly limit filter choices to 1, 0, and All
        selectInput(
          inputId = "pn_filter",
          label = "Filtrér efter pn:",
          choices = c("All", "1", "0"),  # Fixed filter choices
          selected = "All"
        )
      })
      
      # Render the filtered table
      output$effectuatedTable <- renderDT({
        data <- effectuation_data
        
        # Apply the `pn` filter if selected
        if (!is.null(input$pn_filter) && input$pn_filter != "All") {
          data <- data %>% filter(pn == as.numeric(input$pn_filter))  # Convert input to numeric
        }
        
        # Render the filtered table
        datatable(
          data, 
          editable = TRUE, 
          options = list(pageLength = 100)
        )
      })
    } else {
      # Clear the table when no data is available
      output$effectuatedTable <- renderDT(NULL)
    }
  })
  
  
  ################## Nyrefunction tab functionality #########################
  # Render renal recommendations based on data
  observe({
    # Check if eGFR input is NULL, NA, or empty
    if (is.null(input$eGFR) || input$eGFR == "" || is.na(as.numeric(input$eGFR))) {
      output$renal_recommendations <- renderUI({
        p("Giv en eGFR værdi i Input fanen for information om nyrefunktion.")
      })
      return()  # Exit early if eGFR is not valid
    }
    
    # Ensure input$eGFR is numeric
    eGFR <- as.numeric(input$eGFR)
    if (!is.null(values$data) && input$eGFR <= 60) { # Check if `values$data` is not NULL and the eGFR input value is <= 60
      # Load eGFR data
      promed_data <- read_csv("data/all_egfr_data.csv", show_col_types = FALSE)
      
      # Create lookup table for drug names
      drug_lookup <- setNames(values$data$`Indholdsstof`, values$data$ATC) # Create a lookup table for drug names based on ATC codes
      lægemiddel_lookup <- setNames(values$data$`Lægemiddel`, values$data$ATC)
      
      # Filter and process recommendations
      renal_recommendations <- promed_data %>%
        filter(ATC %in% names(drug_lookup)) %>%
        distinct(ATC, .keep_all = TRUE) %>%
        filter(!is.na(egfr_range))
      
      # Filter rows where Nyre_sec_exists is TRUE and egfr_range is NA
      other_renal_recommendations <- promed_data %>%
        filter(ATC %in% names(drug_lookup)) %>%
        distinct(ATC, .keep_all = TRUE) %>%
        filter(nyre_sec_exists == TRUE, is.na(egfr_range)) 
      
      
      renal_recommendations <- renal_recommendations %>%
        mutate(
          egfr_min = purrr::map(egfr_min, ~ as.numeric(strsplit(gsub("\\[|\\]", "", .x), ", ")[[1]])),
          egfr_max = purrr::map(egfr_max, ~ as.numeric(strsplit(gsub("\\[|\\]", "", .x), ", ")[[1]]))
        ) %>%
        mutate(index = purrr::map2(egfr_min, egfr_max, ~ {
          # Find the indices where the condition is satisfied
          idx <- which(input$eGFR >= .x & input$eGFR <= .y)
          if (length(idx) > 0) idx else NA
        }))
      
      # If there are valid recommendations, dynamically render UI
      output$renal_recommendations <- renderUI({
        if (nrow(renal_recommendations) > 0) {
          all_recommendations_text <- lapply(1:nrow(renal_recommendations), function(i) {
            atc <- renal_recommendations$ATC[i]
            # Show all recommendations if checkbox is checked
            if (input$show_all_renal) {
              # Show all egfr_ranges if checkbox is checked
              all_ranges <- strsplit(renal_recommendations$egfr_range[i], "; ")[[1]]
              all_ages <- strsplit(renal_recommendations$age[i], "; ")[[1]]
              all_recommendations <- strsplit(renal_recommendations$recommendation[i], "; ")[[1]]
              all_reasons <- strsplit(renal_recommendations$recommendation_reason[i], "; ")[[1]]
              all_warnings <- strsplit(renal_recommendations$warning[i], "; ")[[1]]
              
              paste(lapply(seq_along(all_ranges), function(j) {
                # Handle optional age variable
                age_text <- if (!is.null(all_ages[j]) && !is.na(all_ages[j]) && all_ages[j] != "NA") {
                  paste0(all_ages[j], ": ")
                } else {
                  ""
                }
                # Combine the parts
                sprintf(
                  "-%s (%s): GFR %s: %s, %s, %s%s\n",
                  drug_lookup[atc],
                  lægemiddel_lookup[atc],
                  all_ranges[j],
                  all_recommendations[j],
                  all_reasons[j],
                  age_text,  
                  all_warnings[j]
                )
              }), collapse = "")
              
            } else {
              
              # Find all matching indices for the input eGFR
              selected_indices <- renal_recommendations$index[[i]]  # Get all matching indices
              
              if (is.null(selected_indices) || length(selected_indices) == 0 || all(is.na(selected_indices))) {
                return(NULL)  # Skip this row if no valid index
              }
              
              # Loop through all selected indices to process each matching instance
              output_text <- lapply(selected_indices, function(selected_index) {
                # Extract GFR range
                egfr_range <- strsplit(renal_recommendations$egfr_range[i], "; ")[[1]][selected_index]
                
                # Extract age range, if available
                age_range <- strsplit(renal_recommendations$age[i], "; ")[[1]][selected_index]
                age_text <- if (!is.null(age_range) && !is.na(age_range) && age_range != "NA") {
                  paste0(age_range, ": ")
                } else {
                  ""
                }
                
                # Extract recommendation
                recommendation <- if (grepl(";", renal_recommendations$recommendation[i])) {
                  strsplit(renal_recommendations$recommendation[i], "; ")[[1]][selected_index]
                } else {
                  renal_recommendations$recommendation[i]
                }
                
                # Extract recommendation reason
                recommendation_reason <- if (grepl(";", renal_recommendations$recommendation_reason[i])) {
                  strsplit(renal_recommendations$recommendation_reason[i], "; ")[[1]][selected_index]
                } else {
                  renal_recommendations$recommendation_reason[i]
                }
                
                # Extract warning
                warning <- if (grepl(";", renal_recommendations$warning[i])) {
                  strsplit(renal_recommendations$warning[i], "; ")[[1]][selected_index]
                } else {
                  renal_recommendations$warning[i]
                }
                
                # Create the output string for this index
                sprintf(
                  "-%s (%s): GFR %s: %s, %s, %s%s\n",
                  drug_lookup[atc],
                  lægemiddel_lookup[atc],
                  egfr_range,
                  recommendation,
                  recommendation_reason,
                  age_text,
                  warning
                )
              })
              
              paste(unlist(output_text), collapse = "")
            }  
          }) 
          
          # Process other_renal_recommendations
          other_recommendations_text <- lapply(1:nrow(other_renal_recommendations), function(i) {
            atc <- other_renal_recommendations$ATC[i]
            warning <- other_renal_recommendations$warning[i]
            sprintf(
              "-%s (%s): %s\n",
              drug_lookup[atc],
              lægemiddel_lookup[atc],
              warning
            )
          })
          
          # Combine both into a single text
          combined_text <- paste(
            paste(unlist(all_recommendations_text), collapse = "\n"),
            paste(unlist(other_recommendations_text), collapse = "\n"),
            sep = "\n"  # Add two newlines between the two parts
          )
          
          # Render all recommendations inside a single box with a copy text button
          tagList(
            tags$h4("Lægemiddelinformation om nedsat nyrefunktion"),
            
            # Add the copy button
            tags$button(
              id = "copy_button",
              type = "button",
              class = "btn btn-primary",
              "Kopier tekst"
            ),
            
            # Add the text content inside a div with an ID for JavaScript targeting
            tags$div(
              id = "text_to_copy",  # Unique ID for the text box
              style = "white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;",
              combined_text
              #paste(unlist(all_recommendations_text, other_renal_recommendations), collapse = "\n")
            ),
            
            # Add JavaScript to enable the copy function
            tags$script(HTML("
                document.getElementById('copy_button').addEventListener('click', function() {
                  const text = document.getElementById('text_to_copy').innerText;  // Get the text content
                  navigator.clipboard.writeText(text).then(function() {
                    alert('Teksten er kopieret til udklipsholderen!');  // Confirmation message
                  }, function(err) {
                    alert('Kunne ikke kopiere teksten: ' + err);
                  });
                });
              "))
          )
          
        } else {
          p("No renal recommendations available.")
        }
      })  
      
      
      # Lægemidler med nestede tabeller som skal tjekkes og Links til Nedsat nyrefunktion for de forskellige lægemidler
      output$links_kidney_drugs <- renderUI({
        if (nrow(renal_recommendations) > 0) {
          
          # Filter drugs with nested_table == TRUE
          drugs_to_check <- renal_recommendations %>%
            filter(nested_table == TRUE) %>%
            distinct(ATC, .keep_all = TRUE)
          
          # Standardize column types
          drugs_to_check <- drugs_to_check %>%
            mutate(
              egfr_min = as.character(egfr_min),
              egfr_max = as.character(egfr_max)
            )
          other_renal_recommendations <- other_renal_recommendations %>%
            mutate(
              egfr_min = as.character(egfr_min),
              egfr_max = as.character(egfr_max)
            )
          
          # Combine `drugs_to_check` and `other_renal_recommendations`, keeping only distinct ATC
          drugs_to_check <- bind_rows(
            drugs_to_check %>% select(ATC, everything()),  # Ensure consistent columns
            other_renal_recommendations %>% select(ATC, everything())  # Ensure consistent columns
          ) %>%
            distinct(ATC, .keep_all = TRUE)  # Keep only distinct ATC values
          
          
          # Create clickable drug names for drugs with nested tables
          drugs_text <- lapply(1:nrow(drugs_to_check), function(i) {
            atc <- drugs_to_check$ATC[i]
            url <- promed_data %>% 
              filter(ATC == atc) %>% 
              pull(url) %>% 
              unique()  # Get URL for this ATC
            if (length(url) > 1) {
              url <- url[1]  # Take the first URL if multiple exist
            }
            if (length(url) > 0) {
              tags$a(
                href = url, target = "_blank", style = "color: red; text-decoration: underline;",
                sprintf("-%s (%s)", drug_lookup[atc], lægemiddel_lookup[atc])
              )
            } else {
              sprintf("-%s (%s)", drug_lookup[atc], lægemiddel_lookup[atc])  # Fallback if no URL
            }
          })
          
          # Get distinct clickable URLs
          drugs_with_info <- renal_recommendations %>%
            #filter(nested_table == TRUE) %>%
            distinct(ATC)
          
          drugs_with_info_other <- other_renal_recommendations %>%
            #filter(nested_table == TRUE) %>%
            distinct(ATC)
          
          # Combine unique ATC codes from both datasets
          unique_atc <- bind_rows(drugs_with_info, drugs_with_info_other) %>%
            distinct(ATC)
          
          # Look up in promed_data for distinct ATC codes
          drug_links <- promed_data %>%
            filter(ATC %in% unique_atc$ATC) %>%
            distinct(ATC, .keep_all = TRUE)  # Ensure no duplicate ATC codes
          
          # Create clickable links with drug names
          urls_text <- lapply(1:nrow(drug_links), function(i) {
            atc <- drug_links$ATC[i]
            url <- drug_links$url[i]
            drug_text <- sprintf("-%s (%s)", drug_lookup[atc], lægemiddel_lookup[atc])
            tags$a(href = url, target = "_blank", style = "color: blue; text-decoration: underline;", drug_text)
          })
          
          
          # Combine and render
          tagList(
            tags$h4("Lægemidler hvor info kan mangle (skal manuelt kontrolleres):"),
            tags$div(
              style = "white-space: pre-wrap;",  # Ensure line breaks
              do.call(tagList, drugs_text)  # Combine all clickable drug names
            ),
            tags$br(),
            tags$h4("Links til info om alle lægemidler med nedsat nyrefunktion:"),
            tags$div(
              style = "white-space: pre-wrap;",  # Ensure line breaks
              do.call(tagList, urls_text)  # Combine all clickable links
            )
          )
          
          
        } else {
          p("No additional warnings or links available.")
        }
      })
      
      
      
    }
  })
  
  
  #################### Bivirkninger tab functionality ###########################
  # Additional information to display
  output$Bivirkninger_tekst <- renderUI({
    # Combine and render
    tagList(
      tags$h3("Bivirkningsoversigt"),
      tags$div(
        style = "white-space: pre-wrap;",  # Ensure line breaks
        "I tabellen nedenfor vises alle birvirkinger relateret til aktuelle ordinationer. Vælges de bivirkninger, som skal indgå i den generede bivirkningsoversigtstekst som opskrives under tabellen. OBS. på nuværende tidspunkt kan man ikke fravælge bivirkninger igen. Ønsker man at bivirkningsoversigtsteksten viser færre bivirkninger må appen startes på ny. "  # Message
      )
    )
  })
  
  
  filtered_bivirkninger <- reactive({
    req(values$data)  # Ensure values$data exists before calling function
    data <- filtered_bivirkninger_data(values$data)  # Get the table
    if (is.null(data) || nrow(data) == 0) {
      return(data.frame(Meddelelse = "Ingen bivirkninger fundet for de valgte ATC koder."))  # Return a valid dataframe
    }
    return(data)
  })
  
  
  output$bivirkninger_list <- DT::renderDataTable({
    data <-  isolate(filtered_bivirkninger())
    
    # Ensure `data` is not NULL
    if (is.null(data) || nrow(data) == 0) {
      return(data.frame("Ingen bivirkninger fundet for de valgte ATC koder."))
    }
    
    # Exclude `url` from displayed columns
    display_data <- data %>%
      select(-url) %>%  # Remove`url` column
      distinct()  # Remove duplicate rows
    
    # Create a unique identifier for selection tracking
    display_data <- display_data %>%
      mutate(ATC_bivirkning = paste(ATC, bivirkning, sep = "_"))
    
    # Use checkboxes with unique values
    display_data$Vælg <- ifelse(
      display_data$ATC_bivirkning %in% values$selected_ids,
      sprintf('<input type="checkbox" name="selectRow" value="%s" checked>', display_data$ATC_bivirkning),
      sprintf('<input type="checkbox" name="selectRow" value="%s">', display_data$ATC_bivirkning)
    )
    
    # Drop `ATC_bivirkning` so it is not shown in the table
    display_data <- display_data %>% select(-ATC_bivirkning)
    
    
    # Keep "Vælg" as the first column
    display_data <- display_data[, c("Vælg", setdiff(names(display_data), "Vælg"))]
    
    DT::datatable(
      display_data,
      rownames = FALSE,
      escape = FALSE,  # Allow HTML for checkboxes
      selection = "none",  # Use checkboxes instead of DT's row selection
      options = list(
        pageLength = 10,
        autoWidth = TRUE,
        searchHighlight = TRUE,
        stateSave = TRUE  # Preserve page and filters after updates
      )
    )
  }, server = FALSE)
  
  
  # Store selected checkboxes persistently
  values <- reactiveValues(selected_ids = character())
  
  # Observe checkbox selections
  observeEvent(input$selected_checkbox_rows, {
    if (!is.null(input$selected_checkbox_rows)) {
      # Merge new selections with existing ones, avoiding duplicates
      values$selected_ids <- unique(c(values$selected_ids, as.character(input$selected_checkbox_rows)))
    }
  })
  
  # Links for the drug promedicin side effects section
  output$links_side_effects_drugs <- renderUI({
    data <- filtered_bivirkninger()
    
    if (nrow(data) > 0) {
      # Only look at distinct ATC codes (exclude duplicate URLs)
      drugs_distinct_url <- data %>%
        select(ATC, `Lægemiddel`, `Indholdsstof`, url) %>%
        distinct(ATC, .keep_all = TRUE)
      
      
      # Create clickable links with drug names
      urls_text <- lapply(1:nrow(drugs_distinct_url), function(i) {
        url <- drugs_distinct_url$url[i]
        drug_text <- sprintf("-%s (%s)",
                             drugs_distinct_url$`Lægemiddel`[i],
                             drugs_distinct_url$`Indholdsstof`[i]
        )
        
        # Only add a clickable link if the URL exists
        if (!is.na(url) && url != "") {
          tags$a(href = url, target = "_blank", style = "color: blue; text-decoration: underline;", drug_text)
        } else {
          tags$span(drug_text)  # Display as plain text if URL is missing
        }
      })
      
      # Combine and render
      tagList(
        tags$h4("Links til info om bivirkninger for alle lægemidlerne:"),
        tags$div(
          style = "white-space: pre-wrap;",  # Ensure line breaks
          do.call(tagList, urls_text)  # Combine all clickable links
        )
      )
    } else {
      p("Links er ikke tilgængelige.")
    }
  })
  
  # Render generated text for selected diagnoses
  generatedTextBivirkninger <- reactive({
    req(values$selected_ids)
    data <- filtered_bivirkninger()
    # Create a composite identifier
    data <- data %>% mutate(ATC_bivirkning = paste(ATC, bivirkning, sep = "_"))
    # Filter based on `ATC_bivirkning`
    selected_data <- data %>% filter(ATC_bivirkning %in% values$selected_ids)
    # Remove duplicates based on key columns
    selected_data <- selected_data %>% distinct(ATC, bivirkning, hyppighed, Lægemiddel, Indholdsstof, .keep_all = TRUE)
    
    if (nrow(selected_data) == 0) {
      return("No data available.")
    }
    
    # Ensure necessary columns exist
    required_columns <- c("bivirkning", "hyppighed", "sværhedsgrad", "Lægemiddel", "Indholdsstof")
    if (!all(required_columns %in% colnames(selected_data))) {
      return("Required columns missing in the dataset.")
    }
    
    # Define the hyppighed categories in order
    hyppighed_order <- c(
      "Meget almindelige (> 10 %)",
      "Almindelige (1-10 %)",
      "Ikke almindelige (0,1-1 %)",
      "Sjældne (0,01-0,1 %)",
      "Meget sjældne (< 0,01 %)",
      "Ikke kendt hyppighed"
    )
    
    # Group by bivirkning
    bivirkning_groups <- split(selected_data, selected_data$bivirkning)
    
    # Generate formatted text for each bivirkning
    texts <- lapply(names(bivirkning_groups), function(bivirkning) {
      biv_data <- bivirkning_groups[[bivirkning]]
      
      # Start text with bivirkning description
      text_output <- paste0("Følgende lægemidler har <b>", bivirkning, "</b> som kendt bivirkning ifølge pro.medicin.dk<br>")
      
      # Loop over hyppighed categories in defined order
      for (hyppighed in hyppighed_order) {
        # Filter rows by the current hyppighed
        hyppighed_data <- biv_data[biv_data$hyppighed == hyppighed, ]
        
        if (nrow(hyppighed_data) > 0) {
          text_output <- paste0(text_output, "<u>", hyppighed, "</u><br>")
          
          # Add each drug entry
          for (i in 1:nrow(hyppighed_data)) {
            drug_entry <- sprintf("- %s (%s), %s",
                                  hyppighed_data$Lægemiddel[i],
                                  hyppighed_data$Indholdsstof[i],
                                  hyppighed_data$sværhedsgrad[i])
            text_output <- paste0(text_output, drug_entry, "<br>")
          }
          text_output <- paste0(text_output, "<br>")  # Add spacing between sections
        }
      }
      
      return(text_output)
    })
    
    return(HTML(paste(texts, collapse = "<br>")))    # Combine all bivirkninger sections
  })
  
  # Render the generated text
  output$generatedTextBivirkninger <- renderUI({
    generatedTextBivirkninger()
  })
  
  
}


# ===========================================
# RUN APPLICATION
# ===========================================
shinyApp(ui = ui, server = server)


