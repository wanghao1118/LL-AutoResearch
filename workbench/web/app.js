"use strict";

async function refreshModules() {
  await Promise.all(Array.from(document.querySelectorAll(".module-status"), async (label) => {
    try {
      const response = await fetch(`/${label.dataset.module}/api/health`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (data.status !== "ok") throw new Error("Service unavailable");
      label.textContent = "服务已连接";
      label.className = "module-status connected";
    } catch (_) {
      label.textContent = "服务未连接";
      label.className = "module-status failed";
    }
  }));
  window.setTimeout(refreshModules, 10000);
}
refreshModules();
