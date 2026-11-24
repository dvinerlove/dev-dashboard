# Packaging manifests

Templates for package-manager submissions. `<SHA256>` placeholders are filled
from the `.sha256` file attached to each GitHub release.

## winget (microsoft/winget-pkgs)

Copy the three `Dvinerlove.DevDashboard*.yaml` files to
`manifests/d/Dvinerlove/DevDashboard/<version>/` in a winget-pkgs fork, replace
`<SHA256>`, validate with `wingetcreate` or `winget validate`, open a PR.
First submission also needs a publisher verification — one-time per publisher.

## scoop (ScoopInstaller/Extras or own bucket)

Copy `dev-dashboard.json` into the `bucket/` folder of a scoop bucket repo,
replace `<SHA256>` (or run `.\bin\checkver.ps1 dev-dashboard -u` which fills it
from `autoupdate.url`). For Extras submission, open a PR against
`ScoopInstaller/Extras` with the manifest only.
