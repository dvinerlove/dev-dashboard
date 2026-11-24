# 58 — Netlify build-info README

- URL: https://github.com/netlify/build/blob/main/packages/build-info/README.md (raw)
- Title: @netlify/build-info — Build Info
- Publisher: GitHub / Netlify (official)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "Build info is the core part of detecting settings and heuristics about the users code. The library is platform agnostic to be used in our React UI, Node.js CLI and build system."
- "It provides a layered approach to detecting the following information: 1. Package Manager 2. Workspaces (pnpm, yarn, npm) 3. Build Systems 4. Frameworks 5. Build Settings"
- API: "the core piece is the Project that needs to be initialized with a file system, the base directory and an optional repository root ... project.getBuildSettings which is running all the other steps as well."
- CLI: "build-info [projectDirectory] --rootDir /project/root/dir" — supports monorepo base-dir vs repo-root distinction.
