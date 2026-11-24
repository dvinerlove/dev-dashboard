# 55 — Vercel @vercel/frameworks types.ts

- URL: https://github.com/vercel/vercel/blob/main/packages/frameworks/src/types.ts (raw)
- Title: packages/frameworks/src/types.ts — Framework detection types
- Publisher: GitHub / Vercel (official source code)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- FrameworkDetectionItem: "path?: string — A file path to detect ... matchContent?: string — A matcher for the entire file ... matchPackage?: string — A matcher for a package specifically found in a \"package.json\" file ... fallback?: boolean — If true, this detector only wins when no non-fallback framework detector matches."
- Framework.detectors: "every?: FrameworkDetectionItem[] — Collection of detectors that must be matched ... some?: — where one match triggers the framework to be detected."
- settings: installCommand/buildCommand/devCommand/outputDirectory, each a Setting with `value` + `placeholder` ("shown in the UI when the user is configuring this setting value"); "ignorePackageJsonScript?: boolean — the builder will not invoke the equivalent script in package.json, and instead will invoke the command specified in configuration setting directly".
- "envPrefix?: string — The environment variable prefix used to inline values into the browser bundle. @example \"NEXT_PUBLIC_\""
- "sort?: number — A ponderated value to sort matching frameworks"
- "detectionConfidence?: 'weak' | 'strong' — `weak` means the detection is commonly incidental (e.g. Storybook as a devDependency of an app that deploys something else), so it should not be used to suggest this framework as an override."
- "supersedes?: string[] — Array of slugs for other framework presets which this framework supersedes."
