# Task generator

This directory is the content-generation boundary for English Sprint.

- `question_schema.json` defines the canonical generated question object.
- `generate_task.py` creates deterministic **draft** templates.
- `example_generated_question.json` is a cross-subject example.
- generated content must pass review/pack validation before it can become `published`.

The generator never writes directly into the Android runtime bank and never marks its own output as published. Future LLM, editor, import-from-past-olympiad and human-authoring pipelines should all emit this same schema.

Example:

```bash
python3 generator/generate_task.py \
  --subject math --grade 6 \
  --competition "Municipal Olympiad" \
  --knowledge MATH.NUMBER.DIVISIBILITY \
  --prerequisite MATH.NUMBER.MULTIPLICATION \
  --seed 42 \
  --output /tmp/task.json
```
