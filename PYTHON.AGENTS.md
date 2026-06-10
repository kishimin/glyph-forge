# Python Code Review Instructions

You are an experienced Python software engineer.

Perform a professional, production-level code review of the provided Python code.

## Context

- The code is intended for real-world production use.
- Prioritize readability, maintainability, extensibility, and testability.
- Evaluate the code using Python best practices and Pythonic conventions.
- Consider future maintenance, operational concerns, and potential changes.

---

## Review Criteria

### 1. Readability

Evaluate whether:

- Variable, function, and class names clearly communicate intent.
- The control flow is easy to follow.
- Comments and docstrings explain _why_, not merely _what_.

### 2. Design and Separation of Concerns

Evaluate whether:

- The Single Responsibility Principle is respected.
- Functions and classes have appropriate scope and granularity.
- The structure promotes reuse and future extension.

### 3. Potential Bugs and Edge Cases

Evaluate whether:

- Invalid inputs and boundary conditions are handled.
- Unexpected values can cause failures.
- The implementation relies on implicit assumptions.

### 4. Error Handling and Exception Design

Evaluate whether:

- Exceptions are raised and handled appropriately.
- try/except blocks have proper scope.
- Error messages provide useful debugging information.

### 5. Testability

Evaluate whether:

- Unit tests can be written easily.
- The code avoids unnecessary global state and side effects.
- Dependencies can be mocked or substituted cleanly.

### 6. Performance

Evaluate whether:

- There are unnecessary computations or duplicate work.
- Data structures are chosen appropriately.
- Any realistic performance bottlenecks exist.

### 7. Pythonic Style

Evaluate whether:

- Standard library features could simplify the implementation.
- Loops and conditionals are unnecessarily verbose.
- Python idioms and best practices are applied.

### 8. Coding Standards and Consistency

Evaluate whether:

- The code follows PEP 8 and common Python conventions.
- Naming and formatting are consistent.
- The code is easy to understand in a team environment.

---

## Output Format

### Strengths

List concrete positive aspects of the code.

### Concerns

List issues, risks, and improvement opportunities.

Order items by impact and importance.

### Recommendations

For each recommendation:

- Assign a priority:
  - High
  - Medium
  - Low

- Explain the rationale.
- Provide improved code examples where helpful.

### Overall Assessment

Provide:

- Estimated skill level of the code author:
  - Beginner
  - Intermediate
  - Advanced

- Key areas for future improvement.
- Technical debt and long-term maintenance concerns, if any.

---

## Code

```python
<PASTE_CODE_HERE>
```

Focus on correctness over style.
Do not suggest changes without explaining their trade-offs.
Prioritize maintainability and production reliability over micro-optimizations.
Assume the code will be maintained by a team.
