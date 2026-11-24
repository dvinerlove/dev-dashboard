# Source 06 — docs/machines (SSH remote dev boxes)

- URL: https://www.getlocalhost.app/docs/machines
- Title: "Run dev servers on another computer over SSH"
- Publisher: getlocalhost.app docs — fetched via r.jina.ai, 2026-11-24
- Tier: L1 | source_class: vendor-authored | cluster: C1

## Key quotes

- "A **Machine** is another computer whose localhost this app shows and controls: a dev box under the desk, a home server, a cloud VM. localhost reaches it with your system's `ssh`… Its Projects show in the sidebar below this computer's."
- "Everything stays on the Machine: its Project Configuration, its Secrets and its Runs. Its Services run there, in its login shell, with its files, and read its Secrets from its own secret store."
- Transport: "localhost runs `ssh <destination> localhost remote --stdio`" — requires BatchMode key auth, trusted host key, localhost installed on remote PATH. "One `ssh` connection per Machine carries everything, and is also an SSH ControlMaster."
- "**Open in Browser** first forwards its Port to the same port on this computer, through the SSH connection… Same number, because `*.localhost` names, OAuth callbacks and cookies expect it." Forward bound to loopback only.
- Reconnect: "A lost connection is made again on its own, after 1 second, then 2, 5, 15, and every 30 seconds". "A Machine counts a connection as ended after 45 seconds without hearing from it."
- "Services you started from here stop on the Machine once the connection ends, unless localhost is open on it."
- Remote projects fully manageable (add/edit/detect services/secrets) once connected; remote folder picker included.
