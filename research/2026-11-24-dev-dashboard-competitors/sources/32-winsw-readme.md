# WinSW README (GitHub, master/v2 branch)

- url: https://raw.githubusercontent.com/winsw/winsw/master/README.md (repo: github.com/winsw/winsw, default branch v3)
- title: Windows Service Wrapper in less restrictive license
- publisher: WinSW project (Jenkins-community origin)
- tier: L1 (official README), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "WinSW is an executable binary, which can be used to wrap and manage a custom process as a Windows service. Once you download the installation package, you can rename WinSW.exe to any name, e.g. MyService.exe." — rename-and-config model, not a central console.

2. "WinSW is being managed by configuration files: Main XML configuration file and Main YAML configuration file." — declarative per-service config, no GUI.

3. Commands: "install to install the service to Windows Service Controller", "uninstall", "start", "stop", "stopwait to stop the service and wait until it's actually stopped", "restart", "status to check the current status of the service" (prints NonExistent/Started/Stopped).

4. "Most commands require Administrator privileges to execute. Since v2.8, WinSW will prompt for UAC in non-elevated sessions."

5. Platform: "WinSW offers executables for .NET Framework 4.6.2+ and .NET 8+."; license MIT.

6. Docs referenced: "Logging and error reporting", "Self-restarting services", "Deferred file operations", "Extensions" — restart/logging exist but configured per-service in XML/YAML.

Note: like NSSM, WinSW is a per-service wrapper for SCM — lifecycle + logging but no dashboard, ports view, or env GUI.
