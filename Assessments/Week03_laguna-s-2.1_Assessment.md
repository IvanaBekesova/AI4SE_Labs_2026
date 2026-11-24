# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 4b out of 5b
- Commentary: The student completed all four tasks with functional deliverables across each. Task 1 selects three valid frameworks from the specified source and formulates corresponding prompts. Task 2 produces prediction files, a comparison report, measured inference times, and a visualization (which could not be viewed as this model does not support image input). Task 3 proposes a non-empty accuracy metric with working implementation code. Task 4 provides comparative analysis but omits a statistical significance test and graph creation, both of which were explicitly required.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: The student chose three distinct prompting frameworks (RTF, ICIO, Few-Shot) from https://frompting.com/frameworks, avoiding ROSES and zero-shot as instructed. The `prompts` file contains well-structured prompts for each framework, tailored to the SQL translation task, including database schema, input/output format, and specific instructions. The `report` explains why each framework was chosen and cites the source URL. The report is brief but adequately covers the required rationale.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: Three prediction files are provided (restaurants_dataset_RTFpredictions.csv, restaurants_dataset_ICIOpredictions.csv, restaurants_dataset_FewShotpredictions.csv), each with `question` and `predicted_sql` columns. The report compares accuracy, correct counts, inference times, and model identification across all three prompts. A visualization.png file is present. Inference times are measured and reported for each prompt. The deliverables meet the task requirements.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposed a "non-empty accuracy" metric that filters out questions with empty expected results, arguing this prevents inflated accuracy from empty answers. The `evaluation` file contains a complete Python implementation that loads the database, evaluates predictions with both standard and non-empty accuracy. The `report` compares the metric values across all three prompts (RTF, ICIO, Few-Shot) and explains the rationale. The implementation is functional and the comparison is clear.

## Task 4
- Awarded: 1b   (max 2b)
- Commentary: The report includes a comparison table with accuracy, non-empty accuracy, and time values for each prompt. It provides analysis of why ICIO performed worst (handling of "some" in questions) versus RTF and Few-Shot, and notes that all ran on the same model. However, the report does not perform or discuss any statistical significance test, which was explicitly required. No graphs or charts are created for Task 4 (the visualization.png belongs to Task 2). The analysis is brief and does not fully consider all factors (e.g., coding agent). These omissions prevent full credit.
