import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

for (const [directory, modulePath] of [
  ["workbench", ""],
  ["auto_search", "auto-search/"],
  ["auto_design", "auto-design/"],
  ["auto_writing", "auto-writing/"],
]) {
  test(`${directory}: file preview offers an HTTP entry without starting requests`, async () => {
    const sourceUrl = new URL(`../../${directory}/web/app.js`, import.meta.url);
    const source = readFileSync(sourceUrl, "utf8");
    const document = {
      body: { innerHTML: "" },
      querySelector() { throw new Error("File preview must not bind task controls"); },
      querySelectorAll() { throw new Error("File preview must not bind task controls"); },
    };
    vm.runInNewContext(source, {
      document,
      location: { protocol: "file:", pathname: fileURLToPath(sourceUrl) },
      fetch() { throw new Error("File preview must not request task APIs"); },
      setTimeout() { throw new Error("File preview must not start polling"); },
    });
    await Promise.resolve();
    assert.match(document.body.innerHTML, /HTML 文件预览/);
    assert.ok(document.body.innerHTML.includes(`href="http://127.0.0.1:8760/${modulePath}"`));
    assert.ok(!document.body.innerHTML.includes("Failed to fetch"));
  });
}

test("Auto Design clears an old connection error after recovery", async () => {
  const nodes = new Map();
  const document = {
    body: { innerHTML: "" },
    querySelector(selector) {
      if (!nodes.has(selector)) nodes.set(selector, {
        textContent: "", hidden: false,
        classList: { add() {}, remove() {} },
        elements: { workspace: { value: "" } },
        replaceChildren() {},
      });
      return nodes.get(selector);
    },
  };
  let offline = true;
  const context = vm.createContext({
    document,
    location: { protocol: "file:", pathname: "/auto-design/" },
    async fetch(url) {
      if (offline) throw new TypeError("Failed to fetch");
      return { ok: true, async json() {
        return url.endsWith("/health") ? { codex_cli: true, workspace: "/fixture" } : { tasks: [] };
      } };
    },
  });
  vm.runInContext(readFileSync(new URL("../../auto_design/web/app.js", import.meta.url), "utf8"), context);
  await vm.runInContext("refresh()", context);
  assert.equal(nodes.get("#notice").textContent, "Failed to fetch");
  offline = false;
  await vm.runInContext("refresh()", context);
  assert.equal(nodes.get("#notice").hidden, true);
  vm.runInContext("notice('输入校验失败')", context);
  await vm.runInContext("refresh()", context);
  assert.equal(nodes.get("#notice").textContent, "输入校验失败");
});
