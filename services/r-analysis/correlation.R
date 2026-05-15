# Correlation analysis module.
# The main callable entrypoint is currently services/r-analysis/analysis_runner.R.
# This file is reserved for splitting the runner into reusable R modules in Phase 3.1.

correlation_notes <- list(
  purpose = "Compute pairwise numeric correlations for filtered regional observations.",
  expected_inputs = c("year", "latitude", "longitude", "metric_value"),
  output = "JSON object with columns and matrix."
)
