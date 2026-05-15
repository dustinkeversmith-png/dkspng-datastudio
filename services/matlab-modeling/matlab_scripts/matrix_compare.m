function result_json = matrix_compare(csv_path, params_json)
%MATRIX_COMPARE MATLAB matrix comparison placeholder.

data = readtable(csv_path);
numericVars = varfun(@isnumeric, data, "OutputFormat", "uniform");
numericData = data{:, numericVars};

result = struct();
result.status = "success";
result.engine = "matlab";
result.mode = "matrix_compare";
result.column_count = size(numericData, 2);
result.row_count = size(numericData, 1);
result.note = "MATLAB matrix comparison implementation hook. Python fallback currently provides active correlation matrix output.";

result_json = jsonencode(result);
end
