# Source 10 — PyInstaller official issue template: "Antiviral false positive or Trojan detection"

- URL: https://github.com/pyinstaller/pyinstaller/blob/develop/.github/ISSUE_TEMPLATE/antivirus.md (raw fetched)
- Publisher: PyInstaller maintainers | Tier: L1/L2 (official project stance) | source_class: vendor-authored (project-authored)
- Fetched: 2026-11-24

## Key verbatim quotes

- "Antiviral false positives are a common theme in distributing software… now that you're entering executable territory, you're also leaving behind the happy little AV free bubble that interpreted languages live in."
- "Distribution tools like PyInstaller will have malware authors amongst its user base and as a result, *machine learning*… based antiviral software respond by blocking anything PyInstaller. This means that, if we change something to improve antivirus detections, the malicious code will change too… This is an indefinite cycle and is why nothing can be done to change PyInstaller."
- "there is no magic `--i-am-not-malware` option (well there is one on Windows (#5579) but it's set already)"
- On `-w/--windowed`: "it's just a reflection of the fact that most people distributing malware using PyInstaller will be using windowed mode." (→ GUI/windowed builds are flagged *more*, not less)
- Mitigations offered verbatim: "Reporting false positives to AV vendors is the correct way"; "Recompiling the bootloaders yourself can make applications better accepted… use gcc instead of the MSVC compiler"; "Purchase codesign certificate for few hundred dollars a year. Note that this is not guaranteed to fix AV false positives but it should make them less common."
- Vendor submission portals listed incl. "Microsoft Defender https://www.microsoft.com/wdsi/filesubmission".

## Signals

- PyInstaller's *official* position: false positives are endemic and unfixable upstream; expected release-doc practice = tell users why the warning appears + give the click-through path (as localhost does), optionally sign; don't expect a flag/option to fix it.
