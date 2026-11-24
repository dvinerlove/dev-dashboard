# Docker Desktop — Dashboard & Containers view (official docs)

- urls: https://docs.docker.com/desktop/use-desktop/ + https://docs.docker.com/desktop/use-desktop/container/
- title: Explore Docker Desktop / Explore the Containers view in Docker Desktop
- publisher: Docker Inc. (docs.docker.com)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "When you open Docker Desktop, the Docker Desktop Dashboard is the first thing you see. It provides a centralized interface to manage your containers, images, volumes, builds, Kubernetes resources, and logs." — the closest big-vendor "local services GUI" pattern.

2. "The Containers view lists all running and stopped containers and applications. It provides a clean interface to manage the lifecycle of your containers, interact with running applications, and inspect Docker objects—including Docker Compose apps."

3. Lifecycle actions: "Start, stop, pause, resume, or restart containers", "Delete containers", "Open a terminal in the container", "Open the port exposed by the container in a browser", "Copy the docker run command for reuse or modification" — open-in-browser-by-port matches our ports feature.

4. Live stats columns: "live stats like CPU %, memory usage/limit, memory %, disk read/write, network I/O, PIDs, and last-started time. Column choices persist between sessions." + "monitor your containers' CPU and memory usage over time".

5. Logs: "Select Logs to view output from the container in real time" with search, timestamps, copy, per-container filtering in multi-container apps.

6. Bulk + grouping: "Select multiple containers or Compose projects ... use the bulk actions toolbar to start, pause, stop, or delete everything selected at once. Compose apps are grouped in the grid with an expand/collapse control." — same idea as our project grouping.

7. AI assist: "each row can surface AI-suggested diagnostic questions and flag detected issues, such as 'Container exited with an error' or 'Container keeps restarting.'" — Docker is shipping crash-loop detection to the UI like our circuit-breaker issues.

8. Inspect shows "local path, version number of the image, SHA-256, port mapping, and other details"; Exec/Debug tabs run commands/debug in containers; Files tab edits container filesystem.

Boundary: manages Docker containers only — no native processes, no arbitrary pet-project processes, no env editing UI, no autorun-of-my-services model (containers have restart policies, but dashboard doesn't manage host autorun).
