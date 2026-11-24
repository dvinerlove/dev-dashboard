# Code signing options for Windows app developers

- URL: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
- Publisher: Microsoft Learn (official Windows docs)
- Tier: L1 | source_class: independent-primary
- Fetched: 2026-11-24 via r.jina.ai, full page

## Key quotes

1. Cost comparison table (verbatim):
   > "| **Microsoft Store (MSIX)** — Store re-signs your package | Free | Worldwide | ✅ No warnings | ✅ Yes | Recommended for most new apps |
   > | **Azure Artifact Signing** (formerly Trusted Signing) | ~$9.99/month | Organizations: USA, Canada, EU, UK. Individuals: USA and Canada only | ⚠️ Reputation builds over time; initial warnings expected | ❌ No | Recommended for non-Store distribution |
   > | **OV certificate** (from a CA such as DigiCert, Sectigo) | $150–300/year | Worldwide | ⚠️ Same as Azure Artifact Signing — reputation builds over time | ❌ No | ... |
   > | **EV certificate** | $400+/year | Worldwide | ⚠️ Same as OV since 2024 — no longer instant bypass | ❌ No | No longer recommended specifically for SmartScreen bypass |"

2. Store MSIX signing is free and automatic:
   > "If you publish your app as an **MSIX package** through the Microsoft Store, code signing is free and handled for you automatically — Microsoft re-signs the package after certification and you don't need to purchase or manage a certificate. If you publish as an **MSI/EXE installer** through the Store, you are responsible for Authenticode signing your installer before submission."

3. Artifact Signing geo limits:
   > "**Geographic limitation:** Azure Artifact Signing is available to organizations in the USA, Canada, the European Union, and the United Kingdom. Individual developers are currently limited to the USA and Canada."

4. OV cert hardware requirement:
   > "**HSM requirement:** As of June 2023, the CA/Browser Forum requires private keys for OV certificates to be stored on a hardware security module (HSM) or hardware token. Most CAs provide a compatible USB token or cloud HSM option."

5. EV change date:
   > "Extended Validation (EV) certificates previously bypassed SmartScreen entirely on first download ... **That behavior was removed in 2024.** EV-signed files now go through the same reputation-building process as OV certificates."

6. Free signing for OSS:
   > "If your project is open source, [SignPath Foundation](https://signpath.io/) offers free code signing for qualifying open-source projects. The program provides OV-level certificate signing through a managed pipeline."

7. MCP server note (directly relevant — our app ships an MCP server):
   > "If your app registers a packaged MCP server so that agents on Windows can use it, production releases must be signed with a certificate that is part of the Microsoft Trusted Root Program. A development certificate is fine for local testing."
