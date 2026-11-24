# 57 — Netlify framework-info README

- URL: https://github.com/netlify/framework-info (raw README, main) — repo MOVED to netlify/build monorepo, package name preserved
- Title: @netlify/framework-info — Framework detection utility
- Publisher: GitHub / Netlify (official)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "Detects which framework a specific website is using. The framework's build/dev commands, directories and server port are also returned."
- Categories: `"static_site_generator"`, `"frontend_framework"` and `"build_tool"` (~30 frameworks: Gatsby, Hugo, Next, Nuxt, CRA, Vue, Angular, Svelte, Expo, Quasar, Parcel, Grunt, Gulp...)
- Detection schema per framework JSON in `/src/frameworks/`: "detect: { npmDependencies: [], excludedNpmDependencies: [], configFiles: [] }"
- "npmDependencies — Any project with one of those packages in their `package.json` (`dependencies` or `devDependencies`) will be considered as using the framework."
- "excludedNpmDependencies — Inverse of `npmDependencies`. If any project is using one of those packages, it will not be considered as using the framework."
- "configFiles — paths relative to the project's directory. Any project with one of configuration files will be considered as using the framework."
- Returned per framework: "dev: { commands: ['gatsby develop'], port: 8000, pollingStrategies: [{ name: 'TCP' }, { name: 'HTTP' }] }, build: { commands: ['gatsby build'], directory: 'public' }, staticAssetsDirectory, env: { GATSBY_LOGGER: 'yurnalist' }, plugins"
