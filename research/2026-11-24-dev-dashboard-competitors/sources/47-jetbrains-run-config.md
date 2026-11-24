# JetBrains IntelliJ — Run/debug configurations doc

- url: https://www.jetbrains.com/help/idea/run-debug-configuration.html
- title: Run/debug configurations | IntelliJ IDEA
- publisher: JetBrains (jetbrains.com/help)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "IntelliJ IDEA uses run/debug configurations to run, debug, and test your code. Each configuration is a named set of startup properties that define what to execute and what parameters and environment should be used." — named service defs with env/args ≈ our service spec, but IDE-scoped.

2. "Temporary — created when you are running a class that does not have a permanent configuration ... Permanent — created explicitly from a template or by saving a temporary configuration. Permanent configurations remain as part of your project until you remove them." — per-project persistence.

3. Docs tree lists "Run multiple configurations" (compound runs) and "Program arguments, VM options, environment variables" pages.

4. "IntelliJ IDEA provides run/debug configuration templates for different languages, tools, and frameworks." — run types bound to toolchain plugins.

Boundary: run configs live inside the IDE project, tied to debugging; no OS-level autorun, port dashboard, crash restart, or cross-project service registry.
