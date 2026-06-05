# Hapa Character Sheet Desktop Shell

This shell wraps the same local Character Sheet prototype in Electron and starts the stdlib Python loopback API when it is not already running.

## Launch

Use the workspace entrypoints:

- `desktop/Launch Hapa Character Sheet.command`
- `desktop/launch-desktop.sh`

The launcher installs Electron dependencies on first run if `node_modules` is missing. A macOS `.app` wrapper can be generated locally, but app bundles are not tracked in git.

## Developer Commands

```bash
cd desktop
npm install
npm start
npm run start:profile
npm run smoke
```

The default route is `#presentation-hero`. Set `HAPA_CHARACTER_SHEET_ROUTE=presentation-profile` before launching to open another section.

Security defaults:

- `nodeIntegration: false`
- `contextIsolation: true`
- `sandbox: true`
- local API stays on `127.0.0.1:8794`

Desktop conveniences:

- Presentation route menu for Hero Detail, Skill Codex, Proof Map, Loadout, Timeline, Profile, Passport, and Data View.
- Single-instance behavior focuses the existing window when launched twice.
- `Open Outputs Folder` menu item opens the generated artifact directory.
