# gethomepage — docs index + services config

- urls: https://gethomepage.dev/ + https://gethomepage.dev/configs/services/
- title: homepage — application dashboard docs
- publisher: gethomepage project (OSS)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "A modern, fast, secure fully proxied, highly customizable application dashboard with integrations for over 100 services and translations into multiple languages. Easily configured via YAML files or through docker label discovery." — the richest home-lab service dashboard; auto-discovery via docker labels is a notable pattern (zero-config service listing).

2. Health display — ICMP: "Services may have an optional ping property that allows you to monitor the availability of an external host. As of v0.8.0, the ping feature attempts to use a true (ICMP) ping command on the underlying host."

3. Health display — HTTP: "Services may have an optional siteMonitor property ... that allows you to monitor the availability of a URL you chose and have the response time displayed. ... The site monitor feature works by making an http HEAD request to the URL, and falls back to GET in case that fails." — read-only probe ≈ our health_url check, display-only.

4. Docker integration: "Services may be connected to a Docker container, either running on the local machine, or a remote machine." + "Clicking on the status label of a service with Docker integration enabled will expand the container stats, where you can see CPU, Memory, and Network activity."

5. Widgets: "Services may also have a service widget (or integration) attached to them" — 100+ per-service widgets (Sonarr/Radarr/Plex/Uptime Kuma/Portainer/Glances/etc.) configured with url + API key in YAML.

6. Auth caveat on probes: siteMonitor "will not, for example, login if the URL requires auth ... usually requires the use of an 'internal' URL".

Boundary: display-only — shows status/stats/links for *existing* services (mostly Docker/homelab); cannot start/stop/restart them, no env, no autorun. Self-hosted web app (Docker/k8s/source), not a native desktop tool.
