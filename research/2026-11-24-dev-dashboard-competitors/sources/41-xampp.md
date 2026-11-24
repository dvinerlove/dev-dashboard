# XAMPP (apachefriends.org + Windows FAQ)

- urls: https://www.apachefriends.org/ + https://www.apachefriends.org/faq_windows.html
- title: XAMPP Installers and Downloads for Apache Friends / XAMPP Windows FAQ
- publisher: Apache Friends
- tier: L1 (official site/docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "XAMPP is a completely free, easy to install Apache distribution containing MariaDB, PHP, and Perl." — Windows, Linux x64, macOS installers (current: 8.5.13, PHP 8.5.13).

2. Control panel scope: "The XAMPP control panel for start/stop Apache, MySQL, FileZilla & Mercury or install these server as services." — minimal 4-service start/stop + SCM install; no ports view, no env editor, no health beyond running state.

3. "Each server in XAMPP you can install also as Windows service. You can also install it from the XAMPP Control Panel. In this case it is necessary to run the scripts or the Control Panel with Administrator privileges." — autorun = Windows services only.

4. "XAMPP is not meant for production use but only for development environments." — dev-only positioning like our dashboard.

5. Batch start/stop: xampp_start.exe / xampp_stop.exe, apache_start.bat, mysql_start.bat etc. — fixed bundled-service set, not extensible to user projects.

Boundary: the original "start/stop my local stack" panel — but frozen at Apache/MySQL/FileZilla/Mercury, no ports/logs/env/issue features, no per-project notion.
