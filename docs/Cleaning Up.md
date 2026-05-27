

# Cleaning Up

1. Fix the imports in the __init__ file
2. Turn the cluster_engine and any other standalone engines in the analysis into just a model and the results inside either define the result as a base class of the resutls inside of the py file itself
3. Same for neighbors, spatial_temporal
4. Move results into their respective place
5. fix imports through each file
6. Add comments along the way
7. Enumerate a document in the format






Modules/{ModuleName}
	What it does
	Basic Usage and Whats Included

# Refactoring & Renaming

Go through and rename each module/submodule
and denote refactors and renaming

1. Got rid of results.py and placed the results data classes directly into the anaylsis models
2. Decouple any plotting from the models and soley focus them on the analysis and data part entirely.



# Module Testing

1. Create a sub folder in tests for each module, and a folder for each submodule and one test for each usage case etc
2. Make each test have multiple function scenarios for each deviation or edge case
3. Make each module test runnable by just using its module name
4. Dont use pytest just make it a normal file with real debug outputs



# Sources
