# Coding standard

Keep code boring, readable, and consistent with the existing architecture.

1. **Python:** four-space indentation, `snake_case` functions/variables, `PascalCase` classes, and `UPPER_CASE` constants. Use standard-library modules unless a dependency has a documented need. Ruff controls import order and formatting; target Python 3.10 syntax.
2. **JavaScript:** modern browser JavaScript, `const` by default, `let` for reassignment, `camelCase`, and no runtime bundler/framework. Prettier controls layout. Keep chart rendering separate from requests and state changes.
3. **HTML/CSS:** semantic elements, meaningful labels, keyboard access, visible focus, responsive layouts, and reduced-motion support. Use design variables instead of scattered color values.
4. **Security:** validate at boundaries, escape repository-controlled text, avoid shell interpolation, never log/persist tokens, and preserve localhost-only deployment. Use synthetic data for tests and screenshots.
5. **Analytics:** normalize to UTC, make inclusive endpoints explicit, retain zero buckets, and distinguish filtered history from latest-revision file data.
6. **Tests/docs:** add regression coverage for fixes, keep default tests offline, explain non-obvious decisions in comments, and update relevant guides with behavior changes.

Use descriptive names and small functions. Avoid speculative abstractions, unrelated refactors, dead code, hardcoded machine paths, and placeholder documentation. Public-facing errors should help users without exposing secrets or raw remote responses.
