# Scoop Wiki — Buckets

- URL: https://github.com/ScoopInstaller/Scoop/wiki/Buckets
- Publisher: ScoopInstaller project wiki (official project docs)
- Tier: L2 | source_class: independent-primary
- Fetched: 2026-11-24 via raw.githubusercontent.com wiki markdown (GitHub wiki pages are a git repo; r.jina.ai was blocked for github.com)

## Key quotes

1. What publishing to scoop means:
   > "In Scoop, buckets are collections of apps. Or, to be more specific, a bucket is a Git repository containing JSON app manifests which describe how to install an app."

2. Official vs own bucket:
   > "Scoop has a main bucket which is bundled with Scoop ... There's an optional extras bucket containing apps that don't quite fit the criteria of the main bucket ... Anyone can set up their own bucket with their own set of apps, and other people can add and install from this bucket—they just need to know the location of the bucket's Git repository."

3. Easy path for indie apps — own bucket template with CI:
   > "You can use the BucketTemplate repository to create the boilerplate for a bucket. ... The template has a bunch of GitHub Actions workflows ... Continuous delivery: An automated workflow runs every 4 hours, which updates all the manifests in the bucket to their latest versions. Issue handlers: Common issues like 404 errors and hash-check failures are handled and corrected automatically."

4. Manifest is trivially small (example verbatim):
   > "'{ version: \"1.0\", url: \"https://gist.github.com/lukesampson/6446238/raw/hello.ps1\", bin: \"hello.ps1\" }' > hello.json"

5. Discovery:
   > "If you want your bucket listed in the Scoop Directory, add a topic of `scoop-bucket` to its github page."

## Note
The Main bucket has separate inclusion criteria (linked page "Criteria-for-including-apps-in-the-main-bucket") — not fetched; open angle. Practical path for a new app: own bucket via BucketTemplate, or PR to Extras bucket.
