# Question Bank Batch Upload Guide

## Overview
The Question Bank now supports **batch upload** functionality, allowing you to upload multiple questions at once from a single file.

## Supported Formats

### 1. TXT/PDF Format (Multiple Questions)
Separate multiple questions using `---` (three or more dashes):

```
Topic: Database Fundamentals
Question: What is a primary key in a relational database?
Option A: A key that unlocks the database
Option B: A unique identifier for each record in a table
Option C: The first column in any table
Option D: A key used for encryption
Correct Answer: B
Score: 10
Difficulty: Easy
Grading Criteria: Student must identify that primary key is a unique identifier
Hint: Think about what makes each row unique

---

Topic: SQL Queries
Question: Which SQL clause is used to filter grouped results?
Option A: WHERE
Option B: HAVING
Option C: FILTER
Option D: GROUP BY
Correct Answer: B
Score: 15
Difficulty: Medium
Grading Criteria: Student must differentiate between WHERE and HAVING clauses
Hint: One filters rows before grouping, one filters after grouping
```

### 2. JSON Array Format (Multiple Questions)
Upload a JSON array containing multiple question objects:

**Multiple Choice Questions:**
```json
[
  {
    "topic": "Database Fundamentals",
    "question": "What is a primary key?",
    "options": [
      "A key that unlocks the database",
      "A unique identifier for each record",
      "The first column in any table",
      "A key used for encryption"
    ],
    "correctAnswer": "B",
    "score": 10,
    "difficulty": "Easy",
    "gradingCriteria": "Must identify unique identifier",
    "hint": "Think about uniqueness"
  },
  {
    "topic": "SQL Queries",
    "question": "Which clause filters grouped results?",
    "options": ["WHERE", "HAVING", "FILTER", "GROUP BY"],
    "correctAnswer": "B",
    "score": 15,
    "difficulty": "Medium",
    "gradingCriteria": "Understand WHERE vs HAVING",
    "hint": "One filters before, one after grouping"
  }
]
```

**Short Answer Questions:**
```json
[
  {
    "topic": "Object-Oriented Programming",
    "question": "Explain polymorphism with an example.",
    "sampleAnswer": "Polymorphism allows objects of different classes to be treated as objects of a common parent class. For example, Shape parent class with Circle and Rectangle children.",
    "keyPoints": "Definition of polymorphism; inheritance; method overriding; real-world example",
    "score": 20,
    "difficulty": "Medium",
    "gradingCriteria": "Must include definition, inheritance relationship, and explanation",
    "hint": "Think about how different shapes implement draw() differently"
  }
]
```

## How to Use

1. **Select Question Type**: Choose "Multiple Choice" or "Short Answer" first
2. **Upload File**: Click "Choose File" and select your TXT, JSON, CSV, or PDF file
3. **Review Questions**: The system will parse and display all questions
4. **Navigate**: Use "Previous" and "Next" buttons to review each question
5. **Edit if Needed**: Modify any question details as necessary
6. **Create All**: Click "Create All X Questions" to batch create

## Field Requirements

### Required Fields (All Questions):
- **Topic**: Subject or category
- **Question**: The actual question text
- **Grading Criteria**: How the question will be graded

### Additional Required Fields:

**Multiple Choice:**
- **Options**: 4 options (A, B, C, D)
- **Correct Answer**: The correct option letter (A, B, C, or D)

**Short Answer:**
- **Sample Answer**: An example of a good answer
- **Key Points**: Main points that should be included

### Optional Fields:
- **Score**: Points for the question (default: 10)
- **Difficulty**: Easy, Medium, or Hard (default: Medium)
- **Hint**: A hint to help students

## Sample Files
Download ready-to-use sample files from the upload dialog:
- 📄 MCQ Batch (TXT)
- 📄 Short Answer Batch (TXT)
- 📄 MCQ Batch (JSON)
- 📄 Short Answer Batch (JSON)

## Tips

1. **Question Separation**: Always use `---` (at least 3 dashes) to separate questions in TXT/PDF files
2. **Type Consistency**: Upload either all MCQ or all Short Answer questions in one file
3. **Validation**: The system will validate each question before creation
4. **Error Handling**: If some questions fail validation, they will be skipped with a detailed report

## Technical Notes

- PDF files are automatically parsed and treated as TXT format
- CSV files follow the same format as TXT files
- JSON format allows for more structured data
- The system automatically detects single vs. batch uploads
- Failed questions won't block the creation of valid questions
