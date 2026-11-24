# VS Code — Port Forwarding doc

- url: https://code.visualstudio.com/docs/editor/port-forwarding (→ /docs/debugtest/port-forwarding)
- title: Port Forwarding — VS Code docs
- publisher: Microsoft (code.visualstudio.com)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "Support for port forwarding is built into Visual Studio Code via Microsoft dev tunnels, no extension required. When running a local web service, you can use the Ports view to make the service accessible to others over the internet." — the Ports view is about *sharing* a port externally, not inventorying/listening-port health.

2. "navigate to the Ports view in the Panel region (Ports: Focus on Ports View), and select Forward a Port."

3. "the Ports view updates to show the port you forwarded and its Forwarded Address. Hovering over the Forwarded Address, you can use the inline actions to copy the address, open it in your browser, or open an in-editor preview."

4. "By default, the forwarded port is Private. ... You can change the visibility by right-clicking on the port and selecting Port Visibility > Public."

Boundary: VS Code knows forwarded/dev-tunnel ports and debug-launched processes; it does not inventory all TCP listeners or let you manage long-running pet services independently of the editor session.
