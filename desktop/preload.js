const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("hapaCharacterSheet", {
  apiBaseUrl: "http://127.0.0.1:8794",
  runtime: "desktop-shell",
  surface: "electron",
});
