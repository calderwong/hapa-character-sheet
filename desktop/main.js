const { app, BrowserWindow, Menu, shell } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

let apiProcess = null;
let mainWindow = null;
const API_HOST = "127.0.0.1";
const API_PORT = 8794;
const DEFAULT_ROUTE = "presentation-hero";

function routeFromArgs() {
  const arg = process.argv.find((item) => item.startsWith("--route="));
  const value = (arg ? arg.slice("--route=".length) : process.env.HAPA_CHARACTER_SHEET_ROUTE) || DEFAULT_ROUTE;
  return String(value).replace(/^#/, "") || DEFAULT_ROUTE;
}

function apiHealthCheck() {
  return new Promise((resolve) => {
    const request = http.get({ host: API_HOST, port: API_PORT, path: "/health", timeout: 600 }, (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.on("timeout", () => {
      request.destroy();
      resolve(false);
    });
    request.on("error", () => resolve(false));
  });
}

async function startApi() {
  if (await apiHealthCheck()) return;
  const root = path.resolve(__dirname, "..");
  apiProcess = spawn("python3", ["-m", "hapa_character_sheet.server"], {
    cwd: root,
    stdio: "inherit",
  });
}

function loadRoute(win, route) {
  const root = path.resolve(__dirname, "..");
  win.loadFile(path.join(root, "outputs", "hapa-character-sheet-prototype.html"), {
    hash: route,
  });
}

function createMenu() {
  const routeItems = [
    ["Hero Detail", "presentation-hero"],
    ["Skill Codex", "presentation-codex"],
    ["Proof Map", "presentation-proof"],
    ["Loadout", "presentation-loadout"],
    ["Timeline", "presentation-timeline"],
    ["Profile", "presentation-profile"],
    ["Passport", "presentation-passport"],
    ["Data View", ""],
  ].map(([label, route]) => ({
    label,
    click: () => {
      if (mainWindow) loadRoute(mainWindow, route);
    },
  }));

  const template = [
    {
      label: "Hapa Character Sheet",
      submenu: [
        { label: "Open Outputs Folder", click: () => shell.openPath(path.resolve(__dirname, "..", "outputs")) },
        { type: "separator" },
        { role: "quit" },
      ],
    },
    { label: "View", submenu: [...routeItems, { type: "separator" }, { role: "reload" }, { role: "toggleDevTools" }] },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow() {
  const route = routeFromArgs();
  const win = new BrowserWindow({
    width: 1440,
    height: 1000,
    minWidth: 1080,
    minHeight: 720,
    title: "Hapa Character Sheet",
    backgroundColor: "#07111c",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });
  mainWindow = win;

  win.once("ready-to-show", () => {
    win.show();
  });

  win.on("closed", () => {
    if (mainWindow === win) mainWindow = null;
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  loadRoute(win, route);
}

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
}

app.on("second-instance", () => {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

app.whenReady().then(async () => {
  await startApi();
  createMenu();
  createWindow();
});

app.on("before-quit", () => {
  if (apiProcess) {
    apiProcess.kill();
    apiProcess = null;
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
