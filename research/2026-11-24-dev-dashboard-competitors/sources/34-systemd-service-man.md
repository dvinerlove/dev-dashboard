# systemd.service(5) man page

- url: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- title: systemd.service — Service unit configuration
- publisher: freedesktop.org / systemd project
- tier: L1 (official man page), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. Restart policy surface: "Takes one of no, on-success, on-failure, on-abnormal, on-watchdog, on-abort, or always. If set to no (the default), the service will not be restarted." — most granular restart taxonomy in the category.

2. Exit-cause matrix (Table 1): clean exit code → on-success/always; unclean exit code → on-failure/always; unclean signal → on-failure/on-abnormal/on-abort/always; timeout and watchdog misses additionally trigger restart under on-failure/on-abnormal/on-watchdog.

3. Guidance: "Setting this to on-failure is the recommended choice for long-running services, in order to increase reliability by attempting automatic recovery from errors."

4. Backoff: "RestartSec= ... Configures the time to sleep before restarting a service ... Defaults to 100ms." + "RestartSteps= ... Configures the number of exponential steps to take to increase the interval of auto-restarts from RestartSec= to RestartMaxDelaySec=. ... values between 3 and 5 are good choices when exponential backoff is desired." — same exponential-backoff model as our dashboard (2→5→10→20s).

5. Watchdog health: "the service must call sd_notify(3) regularly with 'WATCHDOG=1' (i.e. the 'keep-alive ping'). If the time between two such calls is larger than the configured time, then the service is placed in a failed state" — app-cooperative health, not external HTTP/TCP probing.

6. Environment config lives in unit files (systemd.exec: Environment=/EnvironmentFile=) — not covered in this page's fetched portion but implied by config-file model.

Note: systemd is a Linux system init manager — no GUI, no dashboard; scope is OS services, not dev pet-projects.
