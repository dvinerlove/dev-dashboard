# Dashy README (GitHub Lissy93/dashy)

- url: https://raw.githubusercontent.com/Lissy93/dashy/master/README.md
- title: Dashy — homepage for your homelab
- publisher: Lissy93 (MIT, OSS)
- tier: L1 (official README), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "The most customizable dashboard for self-hosters — Dashy is the homepage for your homelab."

2. Feature list: "Real-time status monitoring for each of your apps/links/hosts", "Use widgets to display info and dynamic content from self-hosted services", "Instant search by name, domain, or tags", "Easy single-file YAML-based configuration, and option to configure app through the UI", "100% free and open-source".

3. Status check mechanics: "App/Service status is checked by calling an URL and analyzing its HTTP response code. Host status is checked by sending a real ping ICMP request to the host. Both checks can be done at the same time on the same item."

4. Status display: "display a small status indicator icon. Hovering over it will show additional stats like response time and status code." Polling: "Statuses are checked on page load, but you can allow continuous polling by specifying a time interval between checks, in seconds under appConfig.statusCheckInterval and appConfig.pingCheckInterval." — poll-interval pattern ≈ our 4s probe loop.

5. Deploy: `docker run -p 4000:8080 lissy93/dashy` or Node/Yarn source; config at `./user-data/conf.yml`, editable through UI.

6. Views: "A minimal view, valid for use as a browser start page" + "A workspace view, useful for visiting many apps simultaneously"; launch methods sametab/newtab/modal/workspace.

Boundary: same class as Heimdall/homepage — a *view* onto services that are already running (self-hosted web app); no process control, no ports discovery, no env/autorun. Its value: theming/widgets/status display polish.
