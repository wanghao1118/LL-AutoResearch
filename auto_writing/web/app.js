const state = {
  projects: [],
  activeProject: null,
  activeSection: "intro",
  tab: "workflow",
  pollTimer: null,
  toastTimer: null,
  autoFilledTitle: "",
  editRetainedSupportPaths: [],
  health: null,
};

const sectionLabels = {
  intro: "Introduction",
  related_work: "Related Work",
  method: "Method",
  experiments: "Experiments",
  conclusion: "Conclusion",
  abstract: "Abstract",
};

const requirementLabels = {
  ...sectionLabels,
  intro_research: "Introduction 论文调研",
  related_work_plan: "Related Work 章节规划",
  related_work_research: "Related Work 论文调研",
  reference_insertion: "参考文献调研与插入",
};

const sectionFlows = {
  intro: [
    { kind: "action", key: "intro_research", label: "论文调研", icon: "search" },
    { kind: "section", key: "intro", label: "生成 Introduction", icon: "sparkles" },
  ],
  related_work: [
    { kind: "action", key: "related_work_plan", label: "规划三个 subsection", icon: "list-tree" },
    { kind: "action", key: "related_work_research", label: "论文调研", icon: "search" },
    { kind: "section", key: "related_work", label: "生成 Related Work", icon: "sparkles" },
  ],
};

const statusLabels = {
  empty: "未生成",
  running: "进行中",
  ready: "已完成",
  failed: "失败",
  stale: "需更新",
  partial: "部分完成",
  draft: "待补齐",
};

const pathLabels = {
  experiment_description: "实验说明",
  supporting_materials: "补充资料目录",
  intro_literature_research: "Introduction 调研结果",
  related_work_subsection_plan: "Related Work 三段规划",
  related_work_literature_research: "Related Work 调研结果",
  generated_introduction: "Introduction 输出",
  generated_related_work: "Related Work 输出",
  generated_method: "Method 输出",
  generated_experiments: "Experiments 输出",
  generated_conclusion: "Conclusion 输出",
  generated_abstract: "Abstract 输出",
  reference_bibliography: "参考文献 JSON",
  reference_bib_file: "BibTeX 文件",
  latex_template_source: "LaTeX 模板工作目录",
  latex_package: "LaTeX 下载包",
  compiled_pdf: "编译 PDF",
  resolved_prompts: "Resolved prompts",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function icon(name, className = "") {
  return `<svg class="${className}" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function relativeTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

const moduleBase = location.pathname.startsWith("/auto-writing/") ? "/auto-writing" : "";

async function api(path, options = {}) {
  const response = await fetch(`${moduleBase}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {
    payload = {};
  }
  if (!response.ok) {
    const error = new Error(payload.error || `请求失败 (${response.status})`);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { toast.hidden = true; }, 4200);
}

function projectRunning(project) {
  return Boolean(
    project?.sections?.some((section) => section.status === "running") ||
    project?.actions?.some((action) => action.status === "running") ||
    project?.publication?.status === "running"
  );
}

function sectionByKey(key) {
  return state.activeProject?.sections?.find((item) => item.key === key);
}

function actionByKey(key) {
  return state.activeProject?.actions?.find((item) => item.key === key);
}

function flowForSection(sectionKey) {
  return sectionFlows[sectionKey] || [
    { kind: "section", key: sectionKey, label: `生成 ${sectionLabels[sectionKey]}`, icon: "sparkles" },
  ];
}

function recordForStep(step) {
  return step.kind === "action" ? actionByKey(step.key) : sectionByKey(step.key);
}

function nextStepForSection(sectionKey) {
  const flow = flowForSection(sectionKey);
  const running = flow.find((step) => recordForStep(step)?.status === "running");
  if (running) return running;
  return flow.find((step) => recordForStep(step)?.status !== "ready") || flow[flow.length - 1];
}

function missingText(keys = []) {
  if (!keys.length) return "";
  return `请先完成：${keys.map((item) => requirementLabels[item] || item).join("、")}`;
}

function renderProjectList() {
  const projects = state.projects;
  $("#projectCount").textContent = `${projects.length} 个写作项目`;
  $("#sidebarEmpty").hidden = projects.length > 0;
  $("#projectList").innerHTML = projects.map((project) => {
    const active = state.activeProject?.id === project.id;
    const running = projectRunning(project);
    const progress = running ? "RUN" : `${project.completed}/${project.total}`;
    return `<div class="project-row ${active ? "active" : ""}" data-project-id="${escapeHtml(project.id)}" role="button" tabindex="0">
      ${icon("folder")}
      <span class="project-label"><strong title="${escapeHtml(project.title)}">${escapeHtml(project.title)}</strong><small>${escapeHtml(relativeTime(project.updated_at))} · ${escapeHtml(project.experiment.name)}</small></span>
      <span class="project-progress ${running ? "running" : ""}">${progress}</span>
    </div>`;
  }).join("");
}

function statusBadge(status) {
  return `<span class="status-badge ${status}">${escapeHtml(statusLabels[status] || status)}</span>`;
}

function dependencyText(section) {
  if (section.key === "intro") {
    if (section.missing_requirements.length) return missingText(section.missing_requirements);
    return "论文调研 → 生成";
  }
  if (section.key === "related_work") {
    if (section.missing_requirements.length) return missingText(section.missing_requirements);
    return "规划 3 个 subsection → 论文调研 → 生成";
  }
  if (section.key === "abstract") {
    if (section.missing_requirements.length) return missingText(section.missing_requirements);
    return "全文五个部分完成后生成";
  }
  if (!section.dependencies.length) return "直接读取实验说明";
  const labels = section.dependencies.map((item) => sectionLabels[item]).join(" + ");
  if (section.missing_requirements.length) return missingText(section.missing_requirements);
  return `上文：${labels}`;
}

function renderPipeline() {
  const project = state.activeProject;
  const anyRunning = projectRunning(project);
  $("#sectionPipeline").innerHTML = project.sections.map((section) => {
    const active = state.activeSection === section.key;
    const nextStep = nextStepForSection(section.key);
    const nextRecord = recordForStep(nextStep);
    const missing = nextRecord?.missing_requirements?.length > 0;
    const running = nextRecord?.status === "running";
    const actionIcon = running ? "stop" : missing ? "lock" : nextRecord?.status === "ready" ? "refresh" : nextStep.icon;
    const title = running ? `停止${nextStep.label}` : missing ? missingText(nextRecord.missing_requirements) : nextRecord?.status === "ready" ? `重新${nextStep.label}` : nextStep.label;
    const disabled = anyRunning && !running;
    return `<section class="section-item ${active ? "active" : ""}" data-section="${section.key}">
      <span class="section-index">${String(section.index).padStart(2, "0")}</span>
      <div class="section-info">
        <div class="section-title-row"><h3 class="section-title">${escapeHtml(section.label)}</h3>${statusBadge(section.status)}</div>
        <p class="section-description">${escapeHtml(section.description)}</p>
        <span class="dependency-line ${missing ? "missing" : ""}">${icon(missing ? "lock" : "route")}<span>${escapeHtml(dependencyText(section))}</span></span>
      </div>
      <button class="section-action ${running ? "running" : ""}" type="button" data-run-next-section="${section.key}" title="${escapeHtml(title)}" aria-label="${escapeHtml(title + " " + section.label)}" ${disabled ? "disabled" : ""}>${icon(actionIcon)}</button>
    </section>`;
  }).join("");
}

function inlineLatex(value) {
  let safe = escapeHtml(value);
  safe = safe.replaceAll("\\noindent", "");
  safe = safe.replace(/\\textbf\{([^{}]+)\}/g, "<strong>$1</strong>");
  safe = safe.replace(/\\emph\{([^{}]+)\}/g, "<em>$1</em>");
  return safe;
}

function renderManuscriptContent(content) {
  const output = [];
  let paragraph = [];
  const flush = () => {
    if (!paragraph.length) return;
    output.push(`<p>${inlineLatex(paragraph.join(" "))}</p>`);
    paragraph = [];
  };
  String(content).replaceAll("\r\n", "\n").split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (/^\\(?:begin|end)\{abstract\}$/.test(trimmed)) {
      flush();
      return;
    }
    const heading = trimmed.match(/^\\(?:section|subsection|subsubsection)\{(.+)\}$/);
    if (heading) {
      flush();
      output.push(`<p class="latex-heading">${inlineLatex(heading[1])}</p>`);
    } else if (!trimmed) {
      flush();
    } else {
      paragraph.push(trimmed);
    }
  });
  flush();
  return output.join("");
}

function actionResultSummary(action) {
  if (!action?.content) return "";
  if (action.key === "intro_research") {
    const evidenceCount = action.content.paragraph_1_evidence?.length || 0;
    const paperCount = action.content.paragraph_2_papers?.length || 0;
    return `已整理 ${evidenceCount} 条领域证据和 ${paperCount} 篇代表性论文`;
  }
  if (action.key === "related_work_plan") {
    return (action.content.subsections || []).map((item) => item.title).filter(Boolean).join(" · ");
  }
  if (action.key === "related_work_research") {
    const paperCount = (action.content.subsections || []).reduce((sum, item) => sum + (item.papers?.length || 0), 0);
    return `已按三个 subsection 核验 ${paperCount} 篇论文`;
  }
  return "";
}

function stepButtonLabel(step, record) {
  if (record.status === "running") return "停止";
  if (step.kind === "section") return record.status === "ready" || record.status === "stale" ? "重新生成" : "生成";
  if (step.key.endsWith("_plan")) return record.status === "ready" || record.status === "stale" ? "重新规划" : "开始规划";
  return record.status === "ready" || record.status === "stale" ? "重新调研" : "开始调研";
}

function renderActionWorkflow(section) {
  const flow = flowForSection(section.key);
  const anyRunning = projectRunning(state.activeProject);
  $("#actionWorkflow").innerHTML = `<div class="workflow-heading"><span>MANUAL STEPS</span><strong>每次点击只执行当前一步</strong></div>
    <div class="workflow-steps">${flow.map((step, index) => {
      const record = recordForStep(step);
      const missing = record.missing_requirements || [];
      const running = record.status === "running";
      const disabled = (anyRunning && !running) || missing.length > 0;
      const summary = step.kind === "action" ? actionResultSummary(record) : "";
      const detail = missing.length
        ? missingText(missing)
        : record.error
          ? record.error
          : summary || (record.generated_at ? `完成于 ${relativeTime(record.generated_at)}` : "等待手工启动");
      const dataAttribute = step.kind === "action"
        ? `data-run-action="${step.key}"`
        : `data-generate-section="${step.key}"`;
      const buttonIcon = running ? "stop" : record.status === "ready" || record.status === "stale" ? "refresh" : step.icon;
      return `<div class="workflow-step ${record.status}">
        <span class="workflow-step-index">${index + 1}</span>
        <div class="workflow-step-copy"><div><strong>${escapeHtml(step.label)}</strong>${statusBadge(record.status)}</div><p>${escapeHtml(detail)}</p></div>
        <button class="button workflow-button ${running ? "stop-button" : "secondary"}" type="button" ${dataAttribute} ${disabled ? "disabled" : ""}>${icon(buttonIcon)}<span>${escapeHtml(stepButtonLabel(step, record))}</span></button>
      </div>`;
    }).join("")}</div>`;
}

function renderManuscript() {
  const section = state.activeProject.sections.find((item) => item.key === state.activeSection) || state.activeProject.sections[0];
  state.activeSection = section.key;
  $("#manuscriptKicker").textContent = `SECTION ${String(section.index).padStart(2, "0")}`;
  $("#manuscriptTitle").textContent = section.label;
  const badge = $("#manuscriptStatus");
  badge.className = `status-badge ${section.status}`;
  badge.textContent = statusLabels[section.status] || section.status;
  renderActionWorkflow(section);
  const paper = $("#manuscriptPaper");
  if (section.content) {
    const notice = section.status === "stale" ? `<div class="error-copy">${escapeHtml(section.error || "上文已更新，请重新生成当前部分。")}</div>` : "";
    paper.innerHTML = notice + renderManuscriptContent(section.content);
  } else if (section.status === "running") {
    paper.innerHTML = `<div class="placeholder">${icon("loader", "spin")}<span>Codex 正在生成 ${escapeHtml(section.label)}</span></div>`;
  } else if (section.status === "failed") {
    paper.innerHTML = `<div class="error-copy">${escapeHtml(section.error || "生成失败，请重试。")}</div>`;
  } else if (section.missing_requirements.length) {
    paper.innerHTML = `<div class="placeholder">${icon("lock")}<span>${escapeHtml(dependencyText(section))}</span></div>`;
  } else {
    paper.innerHTML = `<div class="placeholder">${icon("file-text")}<span>尚未生成 ${escapeHtml(section.label)}</span></div>`;
  }
}

function renderPaths() {
  const contract = state.activeProject.path_contract;
  $("#pathContractFile").textContent = state.activeProject.path_contract_path;
  $("#pathTable").innerHTML = Object.entries(contract.entries).map(([key, entry]) => `<div class="path-row">
    <div class="path-key"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(pathLabels[key] || key)}${entry.required ? " · REQUIRED" : ""}</span></div>
    <div class="path-value"><code>${escapeHtml(entry.path)}</code><p>${escapeHtml(entry.description_zh || entry.contains)}</p></div>
  </div>`).join("");
}

function referenceScopeCount(reference, scope) {
  const coverage = reference.content?.coverage;
  if (coverage?.[scope]) return coverage[scope].length;
  return (reference.content?.references || []).filter((item) => item.used_in?.includes(scope)).length;
}

function renderReference() {
  const reference = state.activeProject.reference;
  const badge = $("#referenceStatus");
  badge.className = `status-badge ${reference.status}`;
  badge.textContent = statusLabels[reference.status] || reference.status;
  const locked = reference.missing_requirements.length > 0;
  $("#referenceLocked").hidden = !locked;
  $("#referenceWorkspace").hidden = locked;
  if (locked) {
    const headline = reference.missing_requirements.length === 1 && reference.missing_requirements[0] === "abstract"
      ? "完成 Abstract 后开放"
      : "完成前置写作后开放";
    $("#referenceLocked").innerHTML = `${icon("lock")}<strong>${headline}</strong><span>${escapeHtml(missingText(reference.missing_requirements))}</span>`;
    return;
  }

  const count = reference.reference_count || 0;
  $("#referenceCount").textContent = `${count} / 20–25`;
  let message = "系统会核验现有文献，并为正文与实验设置补齐可追溯引用。";
  if (reference.status === "draft") message = `两次章节调研已沉淀 ${count} 条候选 BibTeX，点击后将补齐并插入全文引用。`;
  if (reference.status === "running") message = "Codex 正在核验论文、数据集、backbone 与 baseline，并插入 LaTeX 引用。";
  if (reference.status === "ready") message = `已完成 ${count} 条参考文献及正文引用插入。`;
  if (reference.status === "stale") message = reference.error || "引用目标已更新，请重新执行参考文献任务。";
  if (reference.status === "failed") message = reference.error || "参考文献任务失败，请重试。";
  $("#referenceMessage").textContent = message;
  $("#referenceMessage").classList.toggle("error", ["failed", "stale"].includes(reference.status));

  const running = reference.status === "running";
  const anyRunning = projectRunning(state.activeProject);
  const button = $("#insertReferences");
  button.className = `button ${running ? "danger" : "primary"}`;
  button.disabled = anyRunning && !running;
  button.innerHTML = running
    ? `${icon("stop")}<span>停止参考文献任务</span>`
    : `${icon(reference.status === "ready" || reference.status === "stale" ? "refresh" : "search")}<span>${reference.status === "ready" || reference.status === "stale" ? "重新调研并插入" : "调研并插入参考文献"}</span>`;

  const scopes = [
    ["intro_p1", "Introduction P1"],
    ["intro_p2", "Introduction P2"],
    ["related_work", "Related Work"],
    ["experiments_datasets", "Datasets"],
    ["experiments_backbones", "Backbones"],
    ["experiments_baselines", "Baselines"],
  ];
  $("#referenceCoverage").innerHTML = scopes.map(([scope, label]) => `<div class="coverage-item"><span>${escapeHtml(label)}</span><strong>${referenceScopeCount(reference, scope)}</strong></div>`).join("");
  const references = reference.content?.references || [];
  $("#referenceList").innerHTML = references.length
    ? references.map((item, index) => `<article class="reference-row">
        <span class="reference-index">${String(index + 1).padStart(2, "0")}</span>
        <div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.authors || "")} · ${escapeHtml(item.year || "")} · ${escapeHtml(item.venue || "")}</p><code>\\cite{${escapeHtml(item.citation_key || "")}}</code></div>
        <a href="${escapeHtml(item.source_url || "#")}" target="_blank" rel="noreferrer" title="打开来源" aria-label="打开 ${escapeHtml(item.title)} 的来源">${icon("route")}</a>
      </article>`).join("")
    : `<div class="reference-empty">尚未收集参考文献。</div>`;
  $("#referencePath").textContent = reference.output_path;
}

function setDownloadState(element, url) {
  element.classList.toggle("disabled", !url);
  element.setAttribute("aria-disabled", url ? "false" : "true");
  element.href = url ? `${moduleBase}${url}` : "#";
}

function renderLatexTemplateSelection() {
  const files = [...$("#latexTemplateFile").files];
  $("#latexTemplateLabel").textContent = files.length ? "重新选择模板 ZIP" : "选择模板 ZIP";
  $("#latexTemplateList").innerHTML = files.map((file, index) => selectedFileMarkup(file, "latex-template", index)).join("");
}

function resetPublicationInput() {
  $("#latexTemplateFile").value = "";
  renderLatexTemplateSelection();
}

function renderPublication() {
  const publication = state.activeProject.publication;
  $("#recompilePublication").hidden = publication.status !== "partial";
  const badge = $("#publicationStatus");
  badge.className = `status-badge ${publication.status}`;
  badge.textContent = statusLabels[publication.status] || publication.status;
  $("#publicationLocked").hidden = publication.available;
  $("#publicationWorkspace").hidden = !publication.available;
  if (!publication.available) {
    $("#publicationLocked").innerHTML = `${icon("lock")}<strong>完成全部内容与参考文献后开放</strong><span>${escapeHtml(missingText(publication.missing_sections))}</span>`;
    return;
  }

  const running = publication.status === "running";
  const selectedTemplate = $("#latexTemplateFile").files[0];
  const build = $("#buildPublication");
  build.className = `button publication-build ${running ? "danger" : "primary"}`;
  build.disabled = !running && !selectedTemplate;
  build.innerHTML = running
    ? `${icon("stop")}<span>停止排版</span>`
    : `${icon("sparkles")}<span>${publication.latex_zip_url ? "重新适配并编译" : "适配并编译"}</span>`;
  $("#latexTemplateFile").disabled = running;

  const template = publication.template;
  let message = "上传期刊或会议提供的 LaTeX 模板 ZIP，系统会识别主 TeX 文件并写入全部章节。";
  if (running) message = `正在适配 ${template?.name || "LaTeX 模板"} 并编译，请保持页面打开。`;
  if (publication.status === "ready") message = `已使用 ${template?.name || "模板"} 完成排版和 PDF 编译。`;
  if (publication.status === "partial") message = `LaTeX 源码已完成，但 PDF 编译未成功：${publication.error || "请检查编译日志。"}`;
  if (publication.status === "failed") message = publication.error || "排版任务失败，请检查模板后重试。";
  if (publication.status === "stale") message = publication.error || "章节已更新，请重新排版发布。";
  $("#publicationMessage").textContent = message;
  $("#publicationMessage").classList.toggle("error", ["partial", "failed", "stale"].includes(publication.status));
  $("#publicationEngine").textContent = publication.compiler
    ? `编译器：${publication.compiler}`
    : publication.compiler_available ? "编译器已就绪" : "未检测到本机 LaTeX 编译器";
  setDownloadState($("#downloadLatex"), publication.latex_zip_url);
  setDownloadState($("#downloadPdf"), publication.pdf_url);
  $("#compileLog").hidden = !publication.compile_log || !publication.error;
  $("#compileLog").textContent = publication.compile_log || "";
}

function renderProject() {
  const project = state.activeProject;
  $("#loadingState").hidden = true;
  $("#workspaceEmpty").hidden = Boolean(project);
  $("#projectView").hidden = !project;
  $("#errorState").hidden = true;
  if (!project) return;
  const automatic = project.automation?.status === "running";
  $("#autoWriting").textContent = automatic ? "暂停自动推进" : "自动完成 / 继续全文与 PDF";
  $("#autoWritingState").textContent = project.automation?.message || "尚未启动自动写作。";
  const projectIndex = Math.max(0, state.projects.findIndex((item) => item.id === project.id));
  $("#projectNumber").textContent = String(projectIndex + 1).padStart(2, "0");
  $("#overallStatus").textContent = `${project.completed} / ${project.total} COMPLETE`;
  $("#projectTitle").textContent = project.title;
  $("#experimentName").textContent = `${project.experiment.name} · ${formatBytes(project.experiment.size)}`;
  $("#supportCount").textContent = `${project.support_files.length} 个补充文件`;
  $("#editProject").disabled = projectRunning(project);
  $("#completionBar").style.width = `${project.total ? project.completed / project.total * 100 : 0}%`;
  renderPipeline();
  renderManuscript();
  renderReference();
  renderPaths();
  renderPublication();
  switchTab(state.tab);
}

function switchTab(tab) {
  state.tab = tab;
  $$("#viewTabs button").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
  $$(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === tab));
}

async function loadProject(projectId, quiet = false) {
  try {
    const changedProject = state.activeProject?.id !== projectId;
    const project = await api(`/api/writings/${encodeURIComponent(projectId)}`);
    state.activeProject = project;
    if (changedProject) resetPublicationInput();
    localStorage.setItem("auto-writing-active-project", project.id);
    const index = state.projects.findIndex((item) => item.id === project.id);
    if (index >= 0) state.projects[index] = { ...state.projects[index], ...project, sections: project.sections.map(({ content, ...item }) => item) };
    renderProjectList();
    renderProject();
    schedulePolling();
  } catch (error) {
    if (!quiet) showFatal(error.message);
  }
}

async function loadProjects() {
  try {
    const result = await api("/api/writings");
    state.projects = result.writings || [];
    renderProjectList();
    if (!state.projects.length) {
      state.activeProject = null;
      renderProject();
      return;
    }
    const remembered = new URLSearchParams(location.search).get("project") || localStorage.getItem("auto-writing-active-project");
    const selected = state.projects.find((item) => item.id === remembered) || state.projects[0];
    await loadProject(selected.id);
  } catch (error) {
    showFatal(error.message);
  }
}

function showFatal(message) {
  $("#loadingState").hidden = true;
  $("#workspaceEmpty").hidden = true;
  $("#projectView").hidden = true;
  $("#errorState").hidden = false;
  $("#errorMessage").textContent = message;
}

function schedulePolling() {
  clearTimeout(state.pollTimer);
  if (!projectRunning(state.activeProject) && state.activeProject?.automation?.status !== "running") return;
  state.pollTimer = setTimeout(async () => {
    if (state.activeProject) await loadProject(state.activeProject.id, true);
  }, 1400);
}

function focusRequirement(key) {
  if (sectionLabels[key]) { state.activeSection = key; state.tab = "workflow"; }
  if (key === "intro_research") { state.activeSection = "intro"; state.tab = "workflow"; }
  if (key === "related_work_plan" || key === "related_work_research") { state.activeSection = "related_work"; state.tab = "workflow"; }
  if (key === "reference_insertion") state.tab = "reference";
  renderPipeline();
  renderManuscript();
  switchTab(state.tab);
}

async function runResearchAction(actionKey) {
  const action = actionByKey(actionKey);
  if (!action) return;
  if (action.missing_requirements.length) {
    showToast(missingText(action.missing_requirements), true);
    focusRequirement(action.missing_requirements[0]);
    return;
  }
  if (action.status === "running" && action.job_id) {
    try {
      await api(`/api/generation/${action.job_id}/cancel`, { method: "POST", body: "{}" });
      showToast(`正在停止 ${action.label}`);
    } catch (error) {
      showToast(error.message, true);
    }
    return;
  }
  try {
    const result = await api(`/api/writings/${state.activeProject.id}/actions/${actionKey}/run`, { method: "POST", body: "{}" });
    state.activeProject = result.project;
    renderProjectList();
    renderProject();
    schedulePolling();
  } catch (error) {
    showToast(error.message, true);
    const missing = error.payload?.missing_requirements || error.payload?.missing_dependencies || [];
    if (missing.length) focusRequirement(missing[0]);
  }
}

function runNextSectionStep(sectionKey) {
  state.activeSection = sectionKey;
  const step = nextStepForSection(sectionKey);
  if (step.kind === "action") runResearchAction(step.key);
  else generateSection(step.key);
}

async function generateSection(sectionKey) {
  const section = sectionByKey(sectionKey);
  state.activeSection = sectionKey;
  renderPipeline();
  renderManuscript();
  if (section.missing_requirements.length) {
    const first = section.missing_requirements[0];
    showToast(dependencyText(section), true);
    focusRequirement(first);
    return;
  }
  if (section.status === "running" && section.job_id) {
    try {
      await api(`/api/generation/${section.job_id}/cancel`, { method: "POST", body: "{}" });
      showToast(`正在停止 ${section.label}`);
    } catch (error) {
      showToast(error.message, true);
    }
    return;
  }
  try {
    const result = await api(`/api/writings/${state.activeProject.id}/sections/${sectionKey}/generate`, { method: "POST", body: "{}" });
    state.activeProject = result.project;
    renderProjectList();
    renderProject();
    schedulePolling();
  } catch (error) {
    showToast(error.message, true);
    const missing = error.payload?.missing_requirements || error.payload?.missing_dependencies || [];
    if (missing.length) focusRequirement(missing[0]);
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || "");
    reader.onerror = () => reject(new Error(`无法读取 ${file.name}`));
    reader.readAsDataURL(file);
  });
}

async function filePayload(file) {
  return { name: file.name, content_base64: await fileToBase64(file) };
}

async function submitNewWriting(event) {
  event.preventDefault();
  const title = $("#writingTitle").value.trim();
  const experiment = $("#experimentFile").files[0];
  const supports = [...$("#supportFiles").files];
  const formError = $("#formError");
  formError.hidden = true;
  if (!title || !experiment) {
    formError.textContent = "请填写写作名称并选择实验说明文件。";
    formError.hidden = false;
    return;
  }
  if (supports.length > 12) {
    formError.textContent = "补充资料最多选择 12 个文件。";
    formError.hidden = false;
    return;
  }
  const submit = $("#createWriting");
  submit.disabled = true;
  submit.textContent = "正在创建";
  try {
    const result = await api("/api/writings", {
      method: "POST",
      body: JSON.stringify({
        title,
        experiment_file: await filePayload(experiment),
        support_files: await Promise.all(supports.map(filePayload)),
      }),
    });
    $("#newWritingDialog").close();
    resetNewWritingForm();
    state.activeProject = result;
    state.activeSection = "intro";
    state.tab = "workflow";
    await loadProjects();
    await loadProject(result.id);
    showToast("写作项目已创建");
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    submit.disabled = false;
    submit.textContent = "创建写作";
  }
}

function selectedFileMarkup(file, kind, index) {
  return `<div class="selected-file">
    ${icon("file-text")}
    <span><strong title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</strong><small>${escapeHtml(formatBytes(file.size))}</small></span>
    <button class="icon-button file-remove" type="button" data-remove-file="${kind}" data-file-index="${index}" title="移除 ${escapeHtml(file.name)}" aria-label="移除 ${escapeHtml(file.name)}">${icon("x")}</button>
  </div>`;
}

function renderSelectedFiles() {
  const experimentFiles = [...$("#experimentFile").files];
  const supportFiles = [...$("#supportFiles").files];
  $("#experimentFileLabel").textContent = experimentFiles.length ? "重新选择实验说明" : "选择实验说明文件";
  $("#supportFilesLabel").textContent = supportFiles.length ? "重新选择补充资料" : "选择参考论文、表格或说明";
  $("#experimentFileList").innerHTML = experimentFiles.map((file, index) => selectedFileMarkup(file, "experiment", index)).join("");
  $("#supportFileList").innerHTML = supportFiles.map((file, index) => selectedFileMarkup(file, "support", index)).join("");
}

function replaceInputFiles(input, files) {
  const transfer = new DataTransfer();
  files.forEach((file) => transfer.items.add(file));
  input.files = transfer.files;
}

function removeSelectedFile(kind, index) {
  const inputs = {
    experiment: $("#experimentFile"),
    support: $("#supportFiles"),
    "edit-experiment": $("#editExperimentFile"),
    "edit-support": $("#editSupportFiles"),
    "latex-template": $("#latexTemplateFile"),
  };
  const input = inputs[kind];
  if (!input) return;
  const files = [...input.files];
  const removed = files[index];
  if (!removed) return;
  replaceInputFiles(input, files.filter((_, fileIndex) => fileIndex !== index));
  if (kind === "experiment" && $("#writingTitle").value.trim() === state.autoFilledTitle) {
    $("#writingTitle").value = "";
    state.autoFilledTitle = "";
  }
  if (kind === "experiment" || kind === "support") renderSelectedFiles();
  if (kind === "edit-experiment" || kind === "edit-support") renderEditProjectFiles();
  if (kind === "latex-template") {
    renderLatexTemplateSelection();
    renderPublication();
  }
}

function resetNewWritingForm() {
  $("#newWritingForm").reset();
  state.autoFilledTitle = "";
  $("#formError").hidden = true;
  $("#formError").textContent = "";
  renderSelectedFiles();
}

function openNewWriting() {
  resetNewWritingForm();
  $("#newWritingDialog").showModal();
  $("#writingTitle").focus();
}

function existingSupportMarkup(file) {
  return `<div class="selected-file">
    ${icon("file-text")}
    <span><strong title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</strong><small>${escapeHtml(formatBytes(file.size))}</small></span>
    <button class="icon-button file-remove" type="button" data-remove-existing-support="${escapeHtml(file.relative_path)}" title="移除 ${escapeHtml(file.name)}" aria-label="移除 ${escapeHtml(file.name)}">${icon("x")}</button>
  </div>`;
}

function renderEditProjectFiles() {
  const experiment = state.activeProject?.experiment;
  const replacement = [...$("#editExperimentFile").files];
  const additions = [...$("#editSupportFiles").files];
  $("#currentExperiment").innerHTML = experiment
    ? `${icon("file-check")}<span><strong>${escapeHtml(experiment.name)}</strong><small>${escapeHtml(formatBytes(experiment.size))}</small></span>`
    : "";
  $("#editExperimentLabel").textContent = replacement.length ? "重新选择替换文件" : "替换实验说明";
  $("#editSupportLabel").textContent = additions.length ? "重新选择新增文件" : "选择新增文件";
  $("#editExperimentList").innerHTML = replacement.map((file, index) => selectedFileMarkup(file, "edit-experiment", index)).join("");
  $("#editSupportList").innerHTML = additions.map((file, index) => selectedFileMarkup(file, "edit-support", index)).join("");
  const retained = new Set(state.editRetainedSupportPaths);
  $("#existingSupportList").innerHTML = state.activeProject.support_files
    .filter((file) => retained.has(file.relative_path))
    .map(existingSupportMarkup)
    .join("") || `<span class="empty-file-list">无保留的补充资料</span>`;
}

function resetEditProjectForm() {
  $("#editProjectForm").reset();
  state.editRetainedSupportPaths = [];
  $("#editFormError").hidden = true;
  $("#editFormError").textContent = "";
}

function openEditProject() {
  if (!state.activeProject || projectRunning(state.activeProject)) return;
  resetEditProjectForm();
  $("#editWritingTitle").value = state.activeProject.title;
  state.editRetainedSupportPaths = state.activeProject.support_files.map((file) => file.relative_path);
  renderEditProjectFiles();
  $("#editProjectDialog").showModal();
  $("#editWritingTitle").focus();
}

async function submitEditProject(event) {
  event.preventDefault();
  if (!state.activeProject) return;
  const title = $("#editWritingTitle").value.trim();
  const experiment = $("#editExperimentFile").files[0];
  const additions = [...$("#editSupportFiles").files];
  const errorCopy = $("#editFormError");
  errorCopy.hidden = true;
  if (!title) {
    errorCopy.textContent = "请填写写作名称。";
    errorCopy.hidden = false;
    return;
  }
  if (state.editRetainedSupportPaths.length + additions.length > 12) {
    errorCopy.textContent = "保留与新增的补充资料合计最多 12 个。";
    errorCopy.hidden = false;
    return;
  }
  const submit = $("#saveProject");
  submit.disabled = true;
  submit.textContent = "正在保存";
  try {
    const result = await api(`/api/writings/${state.activeProject.id}`, {
      method: "PUT",
      body: JSON.stringify({
        title,
        experiment_file: experiment ? await filePayload(experiment) : null,
        retained_support_paths: state.editRetainedSupportPaths,
        new_support_files: await Promise.all(additions.map(filePayload)),
      }),
    });
    $("#editProjectDialog").close();
    state.activeProject = result;
    await loadProjects();
    await loadProject(result.id);
    showToast("项目文件已更新");
  } catch (error) {
    errorCopy.textContent = error.message;
    errorCopy.hidden = false;
  } finally {
    submit.disabled = false;
    submit.textContent = "保存修改";
  }
}

async function buildPublication() {
  const publication = state.activeProject?.publication;
  if (!publication) return;
  if (publication.status === "running" && publication.job_id) {
    try {
      await api(`/api/generation/${publication.job_id}/cancel`, { method: "POST", body: "{}" });
      showToast("正在停止排版任务");
    } catch (error) {
      showToast(error.message, true);
    }
    return;
  }
  const template = $("#latexTemplateFile").files[0];
  if (!template) {
    showToast("请先选择 LaTeX 模板 ZIP。", true);
    return;
  }
  if (template.size > 20 * 1024 * 1024) {
    showToast("LaTeX 模板不能超过 20 MB。", true);
    return;
  }
  const button = $("#buildPublication");
  button.disabled = true;
  try {
    const result = await api(`/api/writings/${state.activeProject.id}/publication/build`, {
      method: "POST",
      body: JSON.stringify({ template_file: await filePayload(template) }),
    });
    state.activeProject = result.project;
    resetPublicationInput();
    renderProjectList();
    renderProject();
    schedulePolling();
  } catch (error) {
    showToast(error.message, true);
    renderPublication();
  } finally {
    button.disabled = false;
  }
}

async function deleteActiveProject() {
  if (!state.activeProject) return;
  try {
    await api(`/api/writings/${state.activeProject.id}`, { method: "DELETE" });
    $("#confirmDialog").close();
    state.activeProject = null;
    localStorage.removeItem("auto-writing-active-project");
    await loadProjects();
    showToast("写作项目已删除");
  } catch (error) {
    showToast(error.message, true);
  }
}

function closeSidebar() {
  $("#sidebar").classList.remove("open");
  $("#sidebarScrim").hidden = true;
}

function bindEvents() {
  $("#autoWriting").addEventListener("click", async (event) => {
    const project = state.activeProject; if (!project) return;
    event.currentTarget.disabled = true;
    try {
      const pausing = project.automation?.status === "running";
      const template = $("#latexTemplateFile").files[0];
      const body = !pausing && template ? { template_file: await filePayload(template) } : {};
      await api(`/api/writings/${project.id}/${pausing ? "auto-pause" : "auto-start"}`, { method: "POST", body: JSON.stringify(body) });
      await loadProject(project.id);
    } catch (error) { showToast(error.message, true); }
    finally { $("#autoWriting").disabled = false; }
  });
  $("#recompilePublication").addEventListener("click", async () => {
    try { await api(`/api/writings/${state.activeProject.id}/recompile`, { method: "POST", body: "{}" }); await loadProject(state.activeProject.id); }
    catch (error) { showToast(error.message, true); }
  });
  $("#writingLogs").addEventListener("click", async () => {
    try {
      const data = await api(`/api/writings/${state.activeProject.id}/logs`);
      $("#writingLogContent").hidden = false;
      $("#writingLogContent").innerHTML = data.logs.map((l) => `<details><summary>${escapeHtml(l.name)}</summary><pre>${escapeHtml(l.text)}</pre></details>`).join("") || "尚无运行日志。";
    } catch (error) { showToast(error.message, true); }
  });
  $("#newWritingButton").addEventListener("click", openNewWriting);
  $("#emptyNewWriting").addEventListener("click", openNewWriting);
  $("#newWritingForm").addEventListener("submit", submitNewWriting);
  $("#newWritingDialog").addEventListener("close", resetNewWritingForm);
  $("#editProject").addEventListener("click", openEditProject);
  $("#editProjectForm").addEventListener("submit", submitEditProject);
  $("#editProjectDialog").addEventListener("close", resetEditProjectForm);
  $("#deleteProject").addEventListener("click", () => $("#confirmDialog").showModal());
  $("#confirmCancel").addEventListener("click", () => $("#confirmDialog").close());
  $("#confirmDelete").addEventListener("click", deleteActiveProject);
  $$('[data-close-dialog]').forEach((button) => button.addEventListener("click", () => $(`#${button.dataset.closeDialog}`).close()));
  $("#experimentFile").addEventListener("change", (event) => {
    const file = event.target.files[0];
    const title = $("#writingTitle");
    if (file && (!title.value.trim() || title.value.trim() === state.autoFilledTitle)) {
      state.autoFilledTitle = file.name.replace(/\.[^.]+$/, "");
      title.value = state.autoFilledTitle;
    }
    renderSelectedFiles();
  });
  $("#supportFiles").addEventListener("change", renderSelectedFiles);
  $("#editExperimentFile").addEventListener("change", renderEditProjectFiles);
  $("#editSupportFiles").addEventListener("change", renderEditProjectFiles);
  $("#latexTemplateFile").addEventListener("change", () => {
    renderLatexTemplateSelection();
    renderPublication();
  });
  $("#buildPublication").addEventListener("click", buildPublication);
  $("#insertReferences").addEventListener("click", () => runResearchAction("reference_insertion"));
  $("#writingTitle").addEventListener("input", (event) => {
    if (event.target.value.trim() !== state.autoFilledTitle) state.autoFilledTitle = "";
  });
  $("#newWritingForm").addEventListener("click", (event) => {
    const remove = event.target.closest("[data-remove-file]");
    if (remove) removeSelectedFile(remove.dataset.removeFile, Number(remove.dataset.fileIndex));
  });
  $("#editProjectForm").addEventListener("click", (event) => {
    const remove = event.target.closest("[data-remove-file]");
    if (remove) {
      removeSelectedFile(remove.dataset.removeFile, Number(remove.dataset.fileIndex));
      return;
    }
    const existing = event.target.closest("[data-remove-existing-support]");
    if (existing) {
      state.editRetainedSupportPaths = state.editRetainedSupportPaths.filter((path) => path !== existing.dataset.removeExistingSupport);
      renderEditProjectFiles();
    }
  });
  $("#latexTemplateList").addEventListener("click", (event) => {
    const remove = event.target.closest("[data-remove-file]");
    if (remove) removeSelectedFile(remove.dataset.removeFile, Number(remove.dataset.fileIndex));
  });
  $("#downloadLatex").addEventListener("click", (event) => {
    if (event.currentTarget.classList.contains("disabled")) event.preventDefault();
  });
  $("#downloadPdf").addEventListener("click", (event) => {
    if (event.currentTarget.classList.contains("disabled")) event.preventDefault();
  });
  $("#projectList").addEventListener("click", (event) => {
    const row = event.target.closest("[data-project-id]");
    if (row) { loadProject(row.dataset.projectId); closeSidebar(); }
  });
  $("#projectList").addEventListener("keydown", (event) => {
    if (!["Enter", " "].includes(event.key)) return;
    const row = event.target.closest("[data-project-id]");
    if (row) { event.preventDefault(); loadProject(row.dataset.projectId); closeSidebar(); }
  });
  $("#sectionPipeline").addEventListener("click", (event) => {
    const action = event.target.closest("[data-run-next-section]");
    if (action) { event.stopPropagation(); runNextSectionStep(action.dataset.runNextSection); return; }
    const item = event.target.closest("[data-section]");
    if (item) { state.activeSection = item.dataset.section; renderPipeline(); renderManuscript(); }
  });
  $("#actionWorkflow").addEventListener("click", (event) => {
    const research = event.target.closest("[data-run-action]");
    if (research) { runResearchAction(research.dataset.runAction); return; }
    const generation = event.target.closest("[data-generate-section]");
    if (generation) generateSection(generation.dataset.generateSection);
  });
  $("#viewTabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-tab]");
    if (button) switchTab(button.dataset.tab);
  });
  $("#sidebarToggle").addEventListener("click", () => {
    $("#sidebar").classList.toggle("open");
    $("#sidebarScrim").hidden = !$("#sidebar").classList.contains("open");
  });
  $("#sidebarScrim").addEventListener("click", closeSidebar);
  window.addEventListener("beforeunload", () => clearTimeout(state.pollTimer));
}

async function checkHealth() {
  try {
    const result = await api("/api/health");
    state.health = result;
    $("#apiState").textContent = result.codex_cli ? "Codex CLI 已就绪" : "Codex CLI 未配置";
    $("#apiState").className = `api-state ${result.codex_cli ? "ready" : "failed"}`;
  } catch (_) {
    $("#apiState").textContent = "本地服务不可用";
    $("#apiState").className = "api-state failed";
  }
}

async function init() {
  if (location.protocol === "file:") {
    document.body.innerHTML = '<main style="max-width:640px;margin:12vh auto;padding:28px;line-height:1.8"><h1>请从本地服务打开 Auto Writing</h1><p>当前是 HTML 文件预览，无法连接任务接口。</p><p><a class="button primary" href="http://127.0.0.1:8760/auto-writing/">打开 Auto Writing 工作台</a></p><p>默认服务地址为 http://127.0.0.1:8760/。如果启动时设置了其他端口，请使用终端显示的地址。</p></main>';
    return;
  }
  bindEvents();
  checkHealth();
  await loadProjects();
}

init();
