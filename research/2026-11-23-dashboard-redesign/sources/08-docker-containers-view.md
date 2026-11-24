# Source 08 — Docker Desktop Containers view docs

- URL: https://docs.docker.com/desktop/use-desktop/container/
- Title: "Explore the Containers view in Docker Desktop"
- Publisher: Docker Inc. docs
- Tier: L1 · source_class: official-docs
- Fetched: 2026-11-23 (via r.jina.ai)

## Key verbatim quotes

1. "The **Containers** view lists all running and stopped containers and applications. It provides a clean interface to manage the lifecycle of your containers, interact with running applications, and inspect Docker objects—including Docker Compose apps."
2. "Toggle **Only show running containers** to hide stopped containers from the grid."
3. "Customize the grid using the **Columns** button. You can show, hide, or reorder columns, including live stats like CPU %, memory usage/limit, memory %, disk read/write, network I/O, PIDs, and last-started time. Column choices persist between sessions."
4. "Select multiple containers or Compose projects using the row checkboxes, then use the bulk actions toolbar to start, pause, stop, or delete everything selected at once."
5. "Compose apps are grouped in the grid with an expand/collapse control. Selecting a project's checkbox selects or deselects all of its containers together." — group rows act as bulk-action scope.
6. Row actions list: "Start, stop, pause, resume, or restart containers … Open a terminal in the container … Open the port exposed by the container in a browser … Copy the `docker run` command."
7. "If Gordon is available, each row can surface AI-suggested diagnostic questions and flag detected issues, such as 'Container exited with an error' or 'Container keeps restarting.'" — inline alert flags on rows.
8. Detail pane: "quick action buttons … or explore the **Logs**, **Inspect**, **Bind mounts**, **Debug**, **Files**, and **Stats** tabs." — secondary actions in tabs, not the row.
9. Log view: search with highlighted matches, copy-all icon, timestamps toggle, clear terminal, per-container filter in multi-container apps, regex/exact match.
