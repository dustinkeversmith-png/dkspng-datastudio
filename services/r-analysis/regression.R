# Regression analysis module.
# The main callable entrypoint is currently services/r-analysis/analysis_runner.R.

regression_notes <- list(
  purpose = "Run simple linear regression over selected x/y fields.",
  example = "metric_value ~ year",
  output = "JSON object with coefficients and model summary."
)
