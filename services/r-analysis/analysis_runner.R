#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(readr)
  library(broom)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  cat(toJSON(list(status = "failed", error = "Usage: Rscript analysis_runner.R <mode> <csv_path> <json_args>"), auto_unbox = TRUE))
  quit(status = 1)
}

mode <- args[[1]]
csv_path <- args[[2]]
json_args <- ifelse(length(args) >= 3, args[[3]], "{}")
params <- fromJSON(json_args)

df <- read_csv(csv_path, show_col_types = FALSE)

safe_numeric_df <- function(df) {
  numeric_cols <- df %>% select(where(is.numeric))
  numeric_cols <- numeric_cols[, colSums(!is.na(numeric_cols)) > 1, drop = FALSE]
  numeric_cols
}

run_correlation <- function(df) {
  numeric_cols <- safe_numeric_df(df)

  if (ncol(numeric_cols) < 2) {
    return(list(
      status = "failed",
      error = "At least two numeric columns are required for correlation.",
      numeric_columns = names(numeric_cols)
    ))
  }

  matrix <- cor(numeric_cols, use = "pairwise.complete.obs")

  list(
    status = "success",
    mode = "correlation",
    columns = colnames(matrix),
    matrix = unname(matrix)
  )
}

run_regression <- function(df, params) {
  x <- ifelse(is.null(params$x), "year", params$x)
  y <- ifelse(is.null(params$y), "metric_value", params$y)

  if (!(x %in% names(df))) {
    return(list(status = "failed", error = paste("Missing x column:", x)))
  }

  if (!(y %in% names(df))) {
    return(list(status = "failed", error = paste("Missing y column:", y)))
  }

  model_df <- df %>%
    select(all_of(c(x, y))) %>%
    mutate(across(everything(), as.numeric)) %>%
    filter(!is.na(.data[[x]]), !is.na(.data[[y]]))

  if (nrow(model_df) < 2) {
    return(list(status = "failed", error = "At least two valid rows are required for regression."))
  }

  formula <- as.formula(paste(y, "~", x))
  model <- lm(formula, data = model_df)

  list(
    status = "success",
    mode = "regression",
    x = x,
    y = y,
    row_count = nrow(model_df),
    coefficients = tidy(model),
    glance = glance(model)
  )
}

run_county_compare <- function(df) {
  if (!("county" %in% names(df))) {
    return(list(status = "failed", error = "Missing county column."))
  }

  value_column <- if ("metric_value" %in% names(df)) "metric_value" else NA

  if (is.na(value_column)) {
    summary <- df %>%
      group_by(county) %>%
      summarize(observation_count = n(), .groups = "drop") %>%
      arrange(desc(observation_count))
  } else {
    summary <- df %>%
      group_by(county) %>%
      summarize(
        observation_count = n(),
        metric_sum = sum(metric_value, na.rm = TRUE),
        metric_mean = mean(metric_value, na.rm = TRUE),
        .groups = "drop"
      ) %>%
      arrange(desc(observation_count))
  }

  list(
    status = "success",
    mode = "county_compare",
    rows = summary
  )
}

result <- switch(
  mode,
  correlation = run_correlation(df),
  regression = run_regression(df, params),
  county_compare = run_county_compare(df),
  list(status = "failed", error = paste("Unknown mode:", mode))
)

cat(toJSON(result, dataframe = "rows", auto_unbox = TRUE, na = "null"))
