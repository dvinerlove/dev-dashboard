# Supervisor documentation — index + introduction

- url: https://supervisord.org/introduction.html (index: https://supervisord.org/)
- title: Introduction — Supervisor 4.3.0 documentation / A Process Control System
- publisher: Supervisor project (supervisord.org)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "Supervisor is a client/server system that allows its users to monitor and control a number of processes on UNIX-like operating systems." / "it is not meant to be run as a substitute for init as 'process id 1' ... meant to be used to control processes related to a project or a customer". — project-scoped process control = closest conceptual match to our app, but Unix-only.

2. "Supervisor will not run at all under any version of Windows." — hard platform boundary; tested on Linux, Mac OS X, Solaris, FreeBSD.

3. Restart: "Supervisord starts processes as its subprocesses, and can be configured to automatically restart them on a crash. It can also automatically be configured to start processes on its own invocation."

4. Features: "Supervisor is configured through a simple INI-style config file ... like restarting failed processes and automatic log rotation." / "Supervisor provides you with one place to start, stop, and monitor your processes. Processes can be controlled individually or in groups. You can configure Supervisor to provide a local or remote command line and web interface."

5. Groups/priority: "processes can be grouped into 'process groups' and a set of logically related processes can be stopped and started as a unit"; "start all" in "preassigned priority order".

6. Web UI: "A (sparse) web user interface with functionality comparable to supervisorctl may be accessed via a browser ... after activating the configuration file's [inet_http_server] section." — built-in but deliberately minimal.

7. API: "The same HTTP server which serves the web UI serves up an XML-RPC interface that can be used to interrogate and control supervisor and the programs it runs." — programmatic control exists (like our HTTP API/MCP).

8. Components: supervisord "is responsible for starting child programs at its own invocation, responding to commands from clients, restarting crashed or exited subprocesseses, logging its subprocess stdout and stderr output, and generating and handling 'events'". No port health checks.
