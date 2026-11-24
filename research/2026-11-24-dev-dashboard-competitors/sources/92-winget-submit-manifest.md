# Submit your manifest to the repository (winget)

- URL: https://learn.microsoft.com/en-us/windows/package-manager/package/repository
- Publisher: Microsoft Learn (Windows Package Manager docs)
- Tier: L1 | source_class: independent-primary
- Fetched: 2026-11-24 via r.jina.ai, full page

## Key quotes

1. Submission mechanism:
   > "To submit your manifest, you'll upload it to the open source https://github.com/microsoft/winget-pkgs repository on GitHub. After you submit a pull request to add a new manifest to the GitHub repository, an automated process will validate your manifest file and check to make sure the package complies with the Windows Package Manager polices and is not known to be malicious."

2. Discretion:
   > "Microsoft reserves the right to refuse a submission for any reason."

3. Local validation first:
   > "The **winget** tool provides the validate command to confirm that you have created your manifest correctly. To validate your manifest, use this command. `winget validate <path-to-the-manifests>`"

4. Repo folder structure:
   > "You must add your manifest files to the repository in the following folder structure: **manifests** / **letter** / **publisher** / **application** / **version**"

5. Expectations for submissions (verbatim list):
   > "* The manifest complies with the schema requirements.
   > * All URLs in the manifest lead to safe websites.
   > * The installer and application are virus free. The package may be identified as malware by mistake. If you believe it is a false positive you can submit the installer to the Microsoft Defender team for analysis.
   > * The application installs and uninstalls correctly for both administrators and non-administrators.
   > * The installer supports non-interactive modes.
   > * All manifest entries are accurate and not misleading.
   > * The installer comes directly from the publisher's website."

6. Common failure: InstallerUrl must be a direct, HTTPS, non-redirected URL from the ISV:
   > "Testing has determined a redirector has been used. This is not allowed because the Windows Package Manager policies require that the InstallerUrl comes directly from the ISV's release location."
