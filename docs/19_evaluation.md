# Evaluation and quality gates

`evals/golden_path.json` contains 30 deterministic scenarios. Each requires all three evidence classes, a non-empty grounded answer, an approval interrupt, and no write before approval. Unit tests exercise both approve and reject branches. CI separately validates Java, Python, UI, and Compose configuration.

The result runner accepts captured result JSON and fails unless all 30 cases pass. Live service evaluation is intentionally distinct from unit testing so infrastructure failures are visible.
