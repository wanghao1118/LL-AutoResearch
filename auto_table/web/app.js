"use strict";

(() => {
  if (location.protocol === "file:") {
    document.body.innerHTML = '<main style="max-width:640px;margin:12vh auto;padding:28px;line-height:1.8"><h1>请从本地服务打开 Auto Table</h1><p>当前是 HTML 文件预览，无法连接任务接口。</p><a href="http://127.0.0.1:8760/auto-table/">打开 AutoResearch 中的 Auto Table</a><p>独立启动时请使用终端显示的地址，默认端口为 8767。</p></main>';
    return;
  }
  const prefix = location.pathname.startsWith("/auto-table/") ? "/auto-table" : "";
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const labels = {idle:"未开始", running:"运行中", ready:"已完成", failed:"运行失败", paused:"已暂停", needs_revision:"需要修改"};
  const steps = [["inspect","读取输入","识别源文件、表格与比较维度"],["design","设计表格","明确科学角色、行列与视觉层级"],["render","生成与替换","保留实验数值与原始来源"],["compile","编译 PDF","生成论文或独立表格预览"],["review","视觉与数据复核","逐页检查排版与证据一致性"]];
  let selected = null;
  let project = null;
  let renderedAt = "";
  let refreshing = false;
  let listMarkup = "";

  async function api(path, payload) {
    const response = await fetch(prefix + path, {cache:"no-store", ...(payload === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})});
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
    return value;
  }
  function error(message, target="notice") { $(target).textContent = message; $(target).hidden = !message; }
  function fileUrl(kind, path) { return `${prefix}/api/projects/${selected}/files/${kind}/${path.split("/").map(encodeURIComponent).join("/")}`; }
  function outputUrl(path) {
    const marker = `/${selected}/`;
    const at = path.indexOf(marker);
    return fileUrl("output", path.slice(at + marker.length));
  }
  function link(path, label, download=false) { return `<a href="${esc(outputUrl(path))}" ${download ? 'download' : 'target="_blank" rel="noopener"'}>${esc(label)}</a>`; }

  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const [listing, health] = await Promise.all([api("/api/projects"),api("/api/health")]);
      $("connection").textContent = `服务已连接${health.codex_cli ? "" : " · 未找到 Codex CLI"}${health.latex ? "" : " · 未找到 LaTeX 编译器"}`;
      $("connection").className = "connection connected";
      $("projectCount").textContent = `${listing.projects.length} 个项目`;
      const nextMarkup = listing.projects.length ? listing.projects.map(p => `<button class="project-row ${p.id === selected ? "active" : ""}" data-project="${p.id}"><strong>${esc(p.title)}</strong><small>${p.mode === "manuscript" ? "论文表格" : "实验数据"} · ${esc(labels[p.status])}</small></button>`).join("") : '<p class="blank">暂无表格项目</p>';
      if (nextMarkup !== listMarkup) { $("projectList").innerHTML = nextMarkup; listMarkup = nextMarkup; }
      if (selected) {
        const value = await api(`/api/projects/${selected}`);
        if (value.id === selected && (value.updated_at !== renderedAt || value.id !== project?.id)) renderProject(value);
      }
    } catch (e) {
      $("connection").textContent = "服务未连接 · " + e.message;
      $("connection").className = "connection";
    } finally { refreshing = false; }
  }
  async function select(id) {
    selected = id;
    renderedAt = "";
    $("sidebar").classList.remove("open");
    error("");
    try { renderProject(await api(`/api/projects/${selected}`)); await refresh(); } catch (e) { error(e.message); }
  }
  function renderProject(value) {
    project = value; renderedAt = value.updated_at;
    $("empty").hidden = true; $("projectView").hidden = false;
    $("projectTitle").textContent = value.title;
    $("projectMode").textContent = value.mode === "manuscript" ? "MANUSCRIPT TABLES" : "EXPERIMENT RESULTS";
    $("projectMeta").textContent = `第 ${value.attempt} 轮 · ${value.inputs.length} 个输入文件 · ${new Date(value.created_at).toLocaleString("zh-CN")}`;
    $("status").textContent = labels[value.status]; $("status").className = "badge " + value.status;
    $("message").textContent = value.message;
    $("progress").style.width = `${value.completed_steps.length / steps.length * 100}%`;
    $("start").hidden = ["running","ready","needs_revision"].includes(value.status);
    $("start").textContent = value.status === "idle" ? "开始整理" : "从当前步骤继续";
    $("stop").hidden = value.status !== "running";
    $("revise").disabled = value.status === "running";
    const bundle = value.artifacts.find(f => f.kind === "output" && f.path === `attempt-${value.attempt}/deliverables.zip`);
    $("bundle").hidden = !bundle;
    if (bundle) $("bundle").href = fileUrl("output",bundle.path);
    $("steps").innerHTML = steps.map(([key,title,description],index) => {
      const done = value.completed_steps.includes(key);
      const active = value.step === key && value.status === "running";
      return `<div class="step ${done ? "complete" : active ? "running" : ""}"><span class="step-number">${done ? "✓" : String(index+1).padStart(2,"0")}</span><div><h3>${title}${active ? " · 进行中" : ""}</h3><p>${description}</p></div></div>`;
    }).join("");
    $("summary").innerHTML = value.rationale ? `<p>${esc(value.rationale)}</p>` : '<p class="muted">完成输入识别后，这里会展示表格角色、比较范围与版式选择。</p>';
    if (value.inspection) {
      const i = value.inspection;
      $("summary").innerHTML += `<p class="muted">${i.table_count !== undefined ? `发现 ${i.table_count} 张表格` : `读取 ${i.record_count ?? "待确认"} 条观测记录`}</p>`;
      if (i.tables) $("summary").innerHTML += i.tables.map(t => `<p><strong>${esc(t.label || t.replacement_file)}</strong><br><small>${esc(t.caption || "无标题")}<br>${esc(t.source_file)}</small></p>`).join("");
    }
    $("review").innerHTML = value.review ? `<div class="review-block"><h3>${value.review.passed ? "复核通过" : "复核需要修改"}</h3><ul>${value.review.findings.map(f => `<li>${esc(f)}</li>`).join("")}</ul><small>已记录 ${value.review.inspected_pages?.length || 0} 个检查页面。完整记录见运行文件。</small></div>` : '<p class="muted">PDF 编译后进行独立复核；未复核的产物不会标记为已完成。</p>';
    renderOutputs(value);
    $("events").innerHTML = '<h2>运行记录</h2>' + value.events.map(e => `<div class="event"><small>${esc(new Date(e.at).toLocaleString("zh-CN"))}</small>${esc(steps.find(s => s[0] === e.step)?.[1] || e.step)} · ${esc(({started:"开始",completed:"完成",failed:"失败",paused:"暂停"})[e.status] || e.status)}${e.message ? `<p>${esc(e.message)}</p>` : ""}</div>`).join("");
    $("files").innerHTML = ["input","output","logs"].map(kind => `<h2>${({input:"原始输入",output:"产物与来源记录",logs:"提示词与执行日志"})[kind]}</h2><div class="file-list">${value.artifacts.filter(f => f.kind === kind).map(f => `<div class="file-row"><a target="_blank" rel="noopener" href="${esc(fileUrl(kind,f.path))}">${esc(f.path)}</a><small>${(f.size / 1024).toFixed(1)} KB</small></div>`).join("")}</div>`).join("");
  }
  function renderOutputs(value) {
    $("outputs").innerHTML = value.outputs.length ? "" : '<p class="blank">表格生成后将在这里显示预览与下载。</p>';
    for (const out of value.outputs) {
      const card = document.createElement("article"); card.className = "output-card";
      card.innerHTML = `<h2>${esc(out.title)}</h2>${out.caption ? `<p>${esc(out.caption)}</p>` : ""}${out.description ? `<p class="muted">${esc(out.description)}</p>` : ""}<div class="output-actions">${out.tex ? link(out.tex,"LaTeX 源码",true) : ""}${out.zip ? link(out.zip,"论文 ZIP",true) : ""}${out.pdf ? link(out.pdf,"PDF 预览 / 下载") : ""}</div>`;
      if (out.manifest?.replaced_tables?.length) {
        const replacements = document.createElement("div"); replacements.className = "output-actions";
        replacements.innerHTML = out.manifest.replaced_tables.map(name => link(`${out.directory}/replacement-tables/${name}`, `替换表格 · ${name}`, true)).join("");
        if (out.manifest.preamble_file) replacements.innerHTML += link(`${out.directory}/replacement-tables/preamble.tex`, "表格样式 · preamble.tex", true);
        card.append(replacements);
      }
      if (out.manifest?.warnings?.length) card.innerHTML += `<p class="muted">${out.manifest.warnings.map(esc).join("<br>")}</p>`;
      if (out.html) {
        const frame = document.createElement("iframe"); frame.className="table-preview"; frame.title=out.title+" HTML 预览"; frame.setAttribute("sandbox",""); frame.src=outputUrl(out.html); card.append(frame);
      }
      if (out.pages?.length) {
        const details = document.createElement("details");
        details.innerHTML = `<summary>查看实际 PDF 页面（${out.pages.length} 页）</summary><div class="pdf-pages">${out.pages.map((p,i)=>`<a target="_blank" rel="noopener" href="${esc(outputUrl(p))}"><img loading="lazy" src="${esc(outputUrl(p))}" alt="第 ${i+1} 页实际 PDF 渲染"></a>`).join("")}</div>`;
        card.append(details);
      }
      $("outputs").append(card);
    }
  }
  async function openCreate() { error("","formError"); $("createDialog").showModal(); await updateMode(); }
  async function updateMode() {
    const mode = new FormData($("createForm")).get("mode");
    $("uploadLabel").hidden = mode === "writing"; $("selectedFiles").hidden = mode === "writing";
    $("writingLabel").hidden = mode !== "writing";
    $("advanced").hidden = mode === "writing";
    $("mainFileLabel").hidden = mode !== "manuscript";
    $("resultSettings").hidden = mode !== "results";
    $("inputFiles").accept = mode === "results" ? ".csv,.tsv,.json,.jsonl" : ".zip,.pdf";
    $("uploadHint").textContent = mode === "results" ? "选择实验结果文件，可上传多个文件" : "选择 LaTeX ZIP，可同时选择参考 PDF";
    if (mode === "writing") {
      try {
        const result = await api("/api/writing-projects");
        $("writingProject").innerHTML = result.projects.length ? result.projects.map(p=>`<option value="${esc(p.id)}">${esc(p.title)}</option>`).join("") : '<option value="">暂无已生成 LaTeX ZIP 的写作项目</option>';
      } catch (e) { error(e.message,"formError"); }
    }
  }
  function encodedFile(file) {
    if (file.size > 20*1024*1024) return Promise.reject(new Error(`${file.name} 超过 20 MB。`));
    return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve({name:file.name,content_base64:reader.result.split(",")[1]});reader.onerror=()=>reject(new Error(`无法读取 ${file.name}`));reader.readAsDataURL(file);});
  }
  $("createForm").addEventListener("submit", async e => {
    e.preventDefault(); const form = e.currentTarget; $("createSubmit").disabled = true; error("","formError");
    try {
      const f=new FormData(form); const mode=f.get("mode"); let created;
      if (mode === "writing") {
        if (!$("writingProject").value) throw new Error("请选择已生成论文的写作项目。");
        created=await api("/api/import-writing",{project_id:$("writingProject").value,title:f.get("title"),requirements:f.get("requirements")});
      } else {
        const files=await Promise.all(Array.from($("inputFiles").files).map(encodedFile));
        if (!files.length) throw new Error("请先选择输入文件。");
        created=await api("/api/projects",{title:f.get("title"),mode,files,requirements:f.get("requirements"),main_file:f.get("main_file"),config:mode === "results" ? JSON.parse(f.get("config") || "{}") : {},manual_config:mode === "results" && f.has("manual_config")});
      }
      $("createDialog").close(); form.reset(); $("selectedFiles").textContent="";
      await select(created.id);
      await api(`/api/projects/${created.id}/start`,{}); await refresh();
    } catch(e) { error(e.message,$("createDialog").open ? "formError" : "notice"); }
    finally { $("createSubmit").disabled=false; }
  });
  $("inputFiles").addEventListener("change",()=>{$("selectedFiles").textContent=Array.from($("inputFiles").files).map(f=>`${f.name} · ${(f.size/1024).toFixed(1)} KB`).join("\n");});
  document.querySelectorAll('[name="mode"]').forEach(el=>el.addEventListener("change",()=>{ $("inputFiles").value="";$("selectedFiles").textContent="";updateMode();}));
  $("newProject").onclick=openCreate; $("emptyNew").onclick=openCreate;
  $("sidebarToggle").onclick=()=>$("sidebar").classList.toggle("open");
  $("projectList").onclick=e=>{const button=e.target.closest("[data-project]");if(button)select(button.dataset.project);};
  document.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>$(b.dataset.close).close());
  document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-tab]").forEach(t=>t.classList.toggle("active",t===b));document.querySelectorAll("[data-panel]").forEach(p=>p.classList.toggle("active",p.dataset.panel===b.dataset.tab));});
  $("start").onclick=async()=>{try{await api(`/api/projects/${selected}/start`,{});error("");await refresh();}catch(e){error(e.message);}};
  $("stop").onclick=async()=>{try{await api(`/api/projects/${selected}/stop`,{});await refresh();}catch(e){error(e.message);}};
  $("revise").onclick=()=>{
    const f=$("reviseForm");f.elements.requirements.value=project.requirements;f.elements.feedback.value="";f.elements.main_file.value=project.main_file||"";f.elements.config.value=JSON.stringify(project.config,null,2);
    $("reviseMainLabel").hidden=project.mode!=="manuscript";$("reviseConfigLabel").hidden=project.mode!=="results";error("","reviseError");$("reviseDialog").showModal();
  };
  $("reviseForm").onsubmit=async e=>{e.preventDefault();$("reviseSubmit").disabled=true;try{const f=new FormData(e.currentTarget);await api(`/api/projects/${selected}/start`,{revise:true,requirements:f.get("requirements"),feedback:f.get("feedback"),main_file:f.get("main_file")||null,config:JSON.parse(f.get("config")||"{}")});$("reviseDialog").close();await refresh();}catch(e){error(e.message,"reviseError");}finally{$("reviseSubmit").disabled=false;}};
  refresh(); window.setInterval(refresh,2500);
})();
