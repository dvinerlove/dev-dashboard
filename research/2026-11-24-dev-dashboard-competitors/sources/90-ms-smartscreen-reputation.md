# SmartScreen reputation for Windows app developers

- URL: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation
- Publisher: Microsoft Learn (official Windows docs)
- Tier: L1 | source_class: independent-primary
- Fetched: 2026-11-24 via r.jina.ai, full page

## Key quotes

1. On what SmartScreen checks:
   > "SmartScreen evaluates two signals when a user downloads and runs a file:
   > 1. **Publisher reputation** — Is the file signed? Is the signing certificate from a known, trusted publisher?
   > 2. **File hash reputation** — Has this specific file been downloaded by users without indications of malicious behavior?"

2. Signed does not mean warning-free:
   > "Even when signed, a newly created binary could still show a SmartScreen warning until its hash or publisher certificate accumulates sufficient evidence of positive reputation."

3. Unsigned = reputation resets each release:
   > "When a file is not signed, SmartScreen reputation must build for each new version of your files, starting with zero reputation. Reputation cannot transfer from previous versions unless both were signed using the same publisher identity."

4. Cert-type table (verbatim):
   > "| Valid Certificate (OV/EV) | ⚠️ Warning — app flagged as unrecognized until reputation accumulates; verified publisher name is displayed |
   > | No signature | ⚠️ Warning — \"Windows protected your PC\"; User must choose \"Run anyway\" before the app can run. Enterprise policy can prevent continuation entirely. |"

5. EV no longer special:
   > "EV certificates no longer bypass SmartScreen. Years ago, signing files with an Extended Validation (EV) code signing certificate would result in positive SmartScreen reputation by default, but this behavior no longer exists. ... Paying a premium for EV solely to avoid SmartScreen warnings is no longer justified."

6. Reputation timeline:
   > "There is no exact threshold, but it can take several weeks and hundreds of clean installs from a wide audience."

7. Store escape hatch:
   > "Store-distributed apps are signed by a Microsoft certificate and are never subject to SmartScreen download warnings."

8. Windows 11 Smart App Control:
   > "On Windows 11 devices, the Smart App Control feature may supersede SmartScreen Application Reputation. Smart App Control will block execution of unsigned files unless the file has a positive reputation."
