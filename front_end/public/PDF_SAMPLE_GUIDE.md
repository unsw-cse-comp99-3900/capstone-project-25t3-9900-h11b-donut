# PDF File Format Guide for Question Upload

## How to Create a PDF File for Upload

To create a PDF file that can be uploaded and parsed:

1. Create a text document with the question information in this format:
2. Save or convert it to PDF format

## PDF Content Format

Your PDF should contain text in the following format:

### For Multiple Choice Questions:

```
Topic: Introduction to Programming
Question: What is a variable in programming?
Score: 10
Difficulty: Easy
Grading Criteria: Must understand basic concept of variables
Hint: Think about where data is stored in memory

Option A: A fixed value that never changes
Option B: A storage location with a name
Option C: A type of function
Option D: A loop structure
Correct Answer: B
```

### For Short Answer Questions:

```
Topic: Data Structures
Question: Explain the concept of a stack data structure and how it works
Score: 15
Difficulty: Medium
Grading Criteria: Must include LIFO concept and basic operations (push, pop)
Hint: Consider how plates are stacked in a cafeteria

Sample Answer: A stack is a Last-In-First-Out (LIFO) data structure where elements are added and removed from the same end, called the top. The two main operations are push (adding an element) and pop (removing the top element).
Key Points: LIFO principle, push operation, pop operation, top element, similar to a stack of plates
```

## Creating PDF Files

### Method 1: Word to PDF
1. Create a Word document with the above format
2. Use "Save As" or "Export" to PDF

### Method 2: Google Docs
1. Create a Google Doc with the above format
2. File → Download → PDF Document

### Method 3: Online Tools
- Use online converters like:
  - smallpdf.com
  - pdf2go.com
  - ilovepdf.com

## Important Notes

- The PDF parser will extract all text from the PDF
- Make sure the text follows the "Field: Value" format
- Each field should be on a separate line
- The parser will automatically detect and fill the corresponding form fields
- PDF text must be selectable (not scanned images)

## Supported Fields

- Topic (主题)
- Question (题目)
- Score (分数)
- Difficulty (难度)
- Grading Criteria (评分标准)
- Hint (提示)

### Multiple Choice Only:
- Option A, Option B, Option C, Option D
- Correct Answer

### Short Answer Only:
- Sample Answer (示例答案)
- Key Points (关键要点)
