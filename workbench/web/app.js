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
if (location.protocol === "file:") {
  document.body.innerHTML = '<main style="max-width:640px;margin:12vh auto;padding:28px;line-height:1.8"><h1>请从本地服务打开 AutoResearch</h1><p>当前是 HTML 文件预览，无法连接任务接口。</p><p><a style="color:#087d70;text-decoration:underline" href="http://127.0.0.1:8760/">打开 AutoResearch 工作台</a></p><p>默认服务地址为 http://127.0.0.1:8760/。如果启动时设置了其他端口，请使用终端显示的地址。</p></main>';
} else {
  refreshModules();
}
