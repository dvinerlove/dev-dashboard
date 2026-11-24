# Chocolatey Community Repository — Moderation

- URL: https://docs.chocolatey.org/en-us/community-repository/moderation/
- Publisher: Chocolatey Software Docs (official)
- Tier: L1 | source_class: independent-primary
- Fetched: 2026-11-24 via r.jina.ai, full page

## Key quotes

1. Human moderation on every version:
   > "The community feed ... is a moderated feed. That means all new versions of packages are human reviewed prior to approval to check for safety, quality, and correctness. ... There are also trusted packages, which only go through automated moderation review and bypass human review as they are coming from trusted sources and/or the software vendors themselves."

2. Automated gates:
   > "the validator — The package validation service checks the quality of a package based on requirements, guidelines and suggestions ... the verifier — The package verifier service checks the correctness (that the package actually works), that it installs and uninstalls correctly, has the right dependencies to ensure it is installed properly and can be installed silently."

3. Metadata requirements (verbatim):
   > "ProjectUrl - it's required for the community feed ... If there is a license available, it **must** be included in the licenseUrl. ... The description should explicitly mention if this package installs trial software or software that needs a license present, or both."

4. Distribution rights:
   > "If binaries are included in the package, does the maintainer have distribution rights? If they have explicit permission, a copy of that in PDF should be in the package contents."

5. Timeout rule:
   > "The cleanup automated check ... checks packages that have been in a 'waiting' ... status with no action/response within 20 days and follows up with a final reminder. If after 15 more days nothing has been done, the package will automatically be rejected on non-response."
