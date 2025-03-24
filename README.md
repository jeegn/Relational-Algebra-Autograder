# Relational-Algebra-Autograder

This repository contains an **automated grading tool for Relational Algebra (RA) expressions written in LaTeX**. It parses RA expressions, translates them into SQL using a modified version of [pyrapt/rapt](https://github.com/pyrapt/rapt), and compares the query output against expected results using a SQLite backend.

---

## Features

- Parses RA expressions written in LaTeX (e.g., from student submissions).
- Converts RA expressions to SQL queries using a customized version of `rapt`.
- Compares SQL output with ground-truth queries.
- Handles disallowed/required RA operators per question.
- Provides detailed feedback with intermediate RA-to-SQL translation.

This project extends [pyrapt/rapt](https://github.com/pyrapt/rapt) with:
- Self-joins and relation aliasing
- Outer joins: left, right, and full
- Intermediate RA expressions via assignment (←)
- Operator restrictions/requirements (per-question)
- Enhanced LaTeX syntax checking and error localization
- Detailed, student-friendly feedback messages
---

## Directory Structure
<pre>
<code>
.
├── AutograderInstructions.pdf     # Guide for students on LaTeX formatting and RA syntax rules
├── LICENSE                        # MIT License (includes attribution to pyrapt/rapt)
├── README.md                      # You’re here!
├── autograder.py                  # Main autograding script
├── grammar.json                   # Grammar for RA parsing
├── rapt/                          # Modified version of pyrapt/rapt
├── run_autograder                 # Entry script for Gradescope
├── solution.json                  # Expected SQL solutions
├── spy.db                         # SQLite DB for executing queries
├── spySchema.json                 # Table schema used in grading
└── student_template.tex           # LaTeX template for student submissions
</code>
</pre>

## Usage

### 1. Prepare the Submission

Students write their answers using `student_template.tex` and follow formatting rules outlined in `AutograderInstructions.pdf`. And place the `.tex` file in the submissions directory (Automatically done via GradeScope)

### 2. Run the Grader

   From the root directory of this repo:
   ```bash
   python autograder.py
