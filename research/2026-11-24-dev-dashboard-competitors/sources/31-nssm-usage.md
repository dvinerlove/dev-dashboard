# NSSM usage (official site)

- url: https://nssm.cc/usage
- title: NSSM - the Non-Sucking Service Manager
- publisher: nssm.cc (Iain Patterson)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "No 'installation' of nssm is needed. Just place it somewhere on the system ... and run it." — single binary, Windows-only tool.

2. Install GUI: "The installer consists of several tabs with lots of configurable parameters." Tabs: Application, Details, Log on, Dependencies, Process, Shutdown, Exit actions, I/O, File rotation, Environment. CLI: "nssm install <servicename> <application> [<options>]" (v2.0+).

3. Per-service env vars: "The Environment tab can be used to specify a newline-separated list of environment variables to pass to the application." Registry: AppEnvironment (replace) / AppEnvironmentExtra (add): "Environment variables set in AppEnvironmentExtra will be added to the service's default environment."

4. Restart throttling (exponential backoff): "If the restarted application continues to exit before running for the threshold amount of milliseconds, nssm will pause for at least 2000 milliseconds, doubling the pause time for each subsequent failure. The maximum time it will pause is 256000 milliseconds, around four minutes." Default AppThrottle 1500 ms.

5. Per-exit-code actions: "To configure the action which nssm should take when the application exits, edit the default value of ... AppExit. ... Change it to either Ignore or Exit to specify the action taken." (default = Restart); per-exit-code overrides under AppExit\<code>.

6. Restart delay: "nssm can apply a mandatory delay between restarts" via AppRestartDelay (ms); "The service will report its state as Paused while waiting for the next restart."

7. Graceful shutdown cascade: "nssm will attempt to generate a Control-C event ... send them a WM_CLOSE message ... send them a WM_QUIT message ... As a last resort nssm can call TerminateProcess()." Configurable per-method timeouts.

8. Log capture via I/O redirection: "Setting Output and Error is usually sufficient to capture log messages"; file rotation incl. online rotation ("nssm reads the application's stdout and/or stderr and writes the output files itself").

Note: no health checks, no port view, no monitoring UI — per-service configuration tool, not a multi-service dashboard.
