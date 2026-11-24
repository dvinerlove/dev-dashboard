# How to auto update a Python desktop app — LicenseSeat

- URL: https://licenseseat.com/python-auto-update
- Publisher: LicenseSeat (software-licensing vendor blog; article claims "checked against each project's own repository, documentation and PyPI page on November 19, 2026")
- Tier: L3 | source_class: vendor-authored
- Fetched: 2026-11-24 via r.jina.ai, full page

## Key quotes

1. PyInstaller ships no updater:
   > "When you freeze a Python app with PyInstaller, you get a folder or an executable ... PyInstaller's documentation doesn't mention updating at all, and neither does Briefcase's. Updating is left to you."

2. Options table (verbatim):
   > "| Velopack | Installer and updater with a Python library | 1.2.161, September 2026 | Active |
   > | tufup | Updater built on The Update Framework | 0.10.0, October 2025 | Quiet for a year, not archived |
   > | PyUpdater | Older updater for PyInstaller apps | 4.0, April 2021 | Archived |
   > | Esky | Older freezer-agnostic updater | 0.9.9, September 2015 | Archived, unmaintained |
   > | pywinsparkle | Python wrapper for WinSparkle | 1.6.0, April 2019 | Dormant, wraps WinSparkle 0.6.0 |"

3. Recommendations (verbatim):
   > "Starting fresh and want an installer and background updates in one tool: **Velopack** ... Don't start anything new on PyUpdater or Esky. Both repositories are archived, and PyUpdater's README opens with 'This is the end'"

4. Velopack + PyInstaller constraint:
   > "Velopack's documentation is explicit about the first line: use `--onedir`, because the single executable from `--onefile` 'is not compatible'. The `vpk` tool needs the .NET SDK on your build machine. Your customers don't need .NET."

5. Windows file-locking reality:
   > "Windows won't let you replace files that are in use. ... So the update has to be applied by something that isn't your app: a separate process, a script, or an installer that runs after your app exits."

6. DIY self-update pattern:
   > "If you already have an installer, the smallest update system is: ask a server for the latest version, compare, download the new installer, verify it, run it, and exit. ... start the installer as a separate process and exit, so the installer can replace your files. The switches shown are Inno Setup's."
   Rules listed verbatim: "Compare versions properly ... Verify what you downloaded against a hash from your feed, over HTTPS ... Sign the installer. A checksum proves the download matches the feed. An Authenticode signature ... is what Windows and SmartScreen check"

7. tufup caveat:
   > "It exits after updating and doesn't relaunch. On Windows it writes a temporary batch file that copies the new files in with `robocopy` after your app quits."
