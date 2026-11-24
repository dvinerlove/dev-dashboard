# Source 04 — docs/environment (env layers + secrets)

- URL: https://www.getlocalhost.app/docs/environment
- Title: "Environment and Secrets"
- Publisher: getlocalhost.app docs — fetched via r.jina.ai, 2026-11-24
- Tier: L1 | source_class: vendor-authored | cluster: C1

## Key quotes

- Layers (later wins): "1. your login shell's environment (on Windows, your user environment as a new sign-in would see it), 2. the Project's variables, 3. the Service's variables, 4. the active Environment Profile's variables (picked in the Project's toolbar), plus `PORT` when it has a Port, and `FORCE_COLOR=1`, `CLICOLOR_FORCE=1`, `PYTHONUNBUFFERED=1` so tools keep their colours and don't buffer output."
- "Click the lock next to a variable to make it a **Secret**: its value goes to your system's secret store and stays hidden until you click the eye. Secret values are never written to configuration files, logs or Project files."
- Secret stores table: "macOS | login Keychain; Linux | the Secret Service: GNOME Keyring, KWallet, KeePassXC; Windows | Credential Manager"
- "Changes apply the next time a Service starts; a running Service shows 'Restart to apply'."
