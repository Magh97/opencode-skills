#!/usr/bin/env node
/**
 * Verificación de instalación de opencode-skills
 *
 * Valida:
 *  1. Frontmatter YAML de todas las skills (name/description obligatorios, name == carpeta)
 *  2. Frontmatter de todos los agentes (description + mode válido)
 *  3. Referencias cruzadas: skills mencionadas en agentes existen en skills/
 *  4. Cobertura de kits según .opencode/kits.tsv (cada skill en >=1 kit, cada kit con >=1 skill)
 *  5. Lint: descripciones fuera de presupuesto, campos desconocidos, presupuesto de auto-invocables
 *  6. Consistencia repo vs instalación (~/.config/opencode) por hash MD5
 *  7. Que los agentes referenciados por business-planning existan
 *
 * Uso: node verify-install.js [--repo-only] [--config <dir>] [--json]
 *   --repo-only    no exige una instalación local; valida solo el repo (modo CI)
 *   --config <dir> ruta al directorio config a verificar (default: ~/.config/opencode)
 * Salida: tabla resumen + códigos de salida (0 ok, 1 con hallazgos)
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

// ── Configuración ────────────────────────────────────────────────
const REPO = path.join(__dirname, "..");
const REPO_SKILLS = path.join(REPO, "skills");
const REPO_AGENTS = path.join(__dirname, "agent");
const KITS_FILE = path.join(__dirname, "kits.tsv");
const README = path.join(REPO, "README.md");

const args = process.argv.slice(2);
const cfgIdx = args.indexOf("--config");
const jsonFlag = args.includes("--json");
const repoOnly = args.includes("--repo-only");
const CFG = cfgIdx !== -1 && args[cfgIdx + 1]
  ? path.resolve(args[cfgIdx + 1])
  : path.join(require("os").homedir(), ".config", "opencode");
const CFG_SKILLS = path.join(CFG, "skills");
const CFG_AGENTS = path.join(CFG, "agent");

const VALID_MODES = ["primary", "all", "subagent"];
const ALLOWED_SKILL_FIELDS = new Set([
  "name", "description", "license", "compatibility", "metadata", "allowed-tools", "disable-model-invocation",
]);
const MAX_AUTO_DESC = 300;   // presupuesto recomendado para skills auto-invocables
const MAX_DISABLED_DESC = 400; // presupuesto para skills desactivadas
const MAX_AUTO_SKILLS = 30;   // cuántas skills puede ver el modelo sin invocación manual
const MAX_AUTO_CHARS = 8000;  // presupuesto total de descripciones auto-invocables

// Agentes que business-planning delega vía task
const BP_DELEGATES = ["planning", "design", "docs"];

const issues = [];
const warnings = [];
const summary = {
  skills: { repo: 0, config: 0, ok: 0, missing: 0, auto: 0, autoChars: 0 },
  agents: { repo: 0, config: 0, ok: 0, missing: 0 },
  frontmatter: { ok: 0, bad: 0 },
  refs: { ok: 0, missing: 0 },
  kits: { kits: 0, uncovered: 0 },
  bp: { ok: 0, missing: 0 },
};

function md5(file) {
  const buf = fs.readFileSync(file);
  const normalized = buf.toString("latin1").replace(/\r\n/g, "\n");
  return crypto.createHash("md5").update(normalized, "latin1").digest("hex");
}

function dirFiles(dir) {
  const out = [];
  const walk = (d, prefix) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(path.join(d, e.name), rel);
      else if (e.isFile()) out.push(rel);
    }
  };
  walk(dir, "");
  return out.sort();
}

function dirDiff(repoDir, cfgDir) {
  const all = new Set([...dirFiles(repoDir), ...dirFiles(cfgDir)]);
  const diff = [];
  for (const rel of [...all].sort()) {
    const r = path.join(repoDir, rel);
    const c = path.join(cfgDir, rel);
    if (!fs.existsSync(c)) diff.push(`${rel} (falta)`);
    else if (!fs.existsSync(r)) diff.push(`${rel} (sobra)`);
    else if (md5(r) !== md5(c)) diff.push(`${rel} (distinto)`);
  }
  return diff;
}

function parseFrontmatter(file) {
  const content = fs.readFileSync(file, "utf8");
  if (!content.startsWith("---")) return { error: "no frontmatter (no empieza con ---)" };
  const end = content.indexOf("\n---", 3);
  if (end === -1) return { error: "frontmatter sin cierre (---)" };
  const raw = content.slice(3, end).replace(/\r/g, "");
  const fm = {};
  const lines = raw.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(/^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$/);
    if (m) {
      let val = m[2].trim();
      if (val === ">" || val === "|") {
        const block = [];
        let j = i + 1;
        while (j < lines.length && lines[j].startsWith("  ")) {
          block.push(lines[j].trim());
          j++;
        }
        val = block.join(" ");
        i = j - 1;
      }
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      fm[m[1]] = val;
    }
  }
  if (fm.name === undefined && fm.description === undefined) {
    return { error: "frontmatter vacío o sin campos reconocibles" };
  }
  return { fm, error: null };
}

function listDirs(dir) {
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && fs.existsSync(path.join(dir, d.name, "SKILL.md")))
    .map((d) => d.name);
}

// ── 0. Carpetas sin SKILL.md ─────────────────────────────────────
const skillDirs = listDirs(REPO_SKILLS);
for (const e of fs.readdirSync(REPO_SKILLS, { withFileTypes: true })) {
  if (e.isDirectory() && !fs.existsSync(path.join(REPO_SKILLS, e.name, "SKILL.md"))) {
    issues.push(`[SKILL] ${e.name}/ no tiene SKILL.md`);
  }
}
summary.skills.repo = skillDirs.length;

// ── 1. Frontmatter + lint de skills ──────────────────────────────
const declaredNames = new Map();
for (const name of skillDirs) {
  const file = path.join(REPO_SKILLS, name, "SKILL.md");
  const { fm, error } = parseFrontmatter(file);
  if (error) {
    summary.frontmatter.bad++;
    issues.push(`[SKILL] ${name}/SKILL.md: ${error}`);
    continue;
  }
  if (!fm.name || !fm.description) {
    summary.frontmatter.bad++;
    issues.push(`[SKILL] ${name}/SKILL.md: falta name y/o description`);
    continue;
  }
  if (fm.name !== name) {
    summary.frontmatter.bad++;
    issues.push(`[SKILL] ${name}/SKILL.md: name (${fm.name}) no coincide con carpeta`);
    continue;
  }
  if (fm.description.length > 1024) {
    issues.push(`[LINT] ${name}: description de ${fm.description.length} chars (máximo del spec: 1024)`);
  }
  const disabled = fm["disable-model-invocation"] !== undefined;
  const limit = disabled ? MAX_DISABLED_DESC : MAX_AUTO_DESC;
  if (fm.description.length > limit) {
    warnings.push(`[LINT] ${name}: description de ${fm.description.length} chars (recomendado <= ${limit}${disabled ? ", desactivada" : ", auto-invocable"})`);
  }
  for (const key of Object.keys(fm)) {
    if (!ALLOWED_SKILL_FIELDS.has(key)) {
      warnings.push(`[LINT] ${name}: campo de frontmatter no soportado por opencode: "${key}" (mover a metadata:)`);
    }
  }
  if (declaredNames.has(fm.name)) {
    issues.push(`[LINT] name duplicado: ${fm.name} (${declaredNames.get(fm.name)} y ${name})`);
  }
  declaredNames.set(fm.name, name);
  if (!disabled) {
    summary.skills.auto++;
    summary.skills.autoChars += fm.description.length;
  }
  summary.frontmatter.ok++;
}
if (summary.skills.auto > MAX_AUTO_SKILLS) {
  issues.push(`[LINT] ${summary.skills.auto} skills auto-invocables (> ${MAX_AUTO_SKILLS}); usa disable-model-invocation: true en las sub-skills`);
}
if (summary.skills.autoChars > MAX_AUTO_CHARS) {
  issues.push(`[LINT] descripciones auto-invocables: ${summary.skills.autoChars} chars (> ${MAX_AUTO_CHARS}); recorta o desactiva`);
}

// ── 2. Frontmatter de agentes ────────────────────────────────────
const agentFiles = fs.readdirSync(REPO_AGENTS).filter((f) => f.endsWith(".md"));
summary.agents.repo = agentFiles.length;
for (const f of agentFiles) {
  const file = path.join(REPO_AGENTS, f);
  const { fm, error } = parseFrontmatter(file);
  if (error) {
    summary.frontmatter.bad++;
    issues.push(`[AGENT] ${f}: ${error}`);
    continue;
  }
  if (!fm.description) {
    summary.frontmatter.bad++;
    issues.push(`[AGENT] ${f}: falta description`);
  }
  if (!fm.mode || !VALID_MODES.includes(fm.mode)) {
    summary.frontmatter.bad++;
    issues.push(`[AGENT] ${f}: mode inválido o faltante (${fm.mode || "?"})`);
  }
  if (fm.mode && VALID_MODES.includes(fm.mode) && fm.description) {
    summary.frontmatter.ok++;
  }
}

// ── 3. Referencias cruzadas: skills mencionadas en agentes ───────
const backtickRefs = [];
for (const f of agentFiles) {
  const file = path.join(REPO_AGENTS, f);
  const content = fs.readFileSync(file, "utf8");
  const refs = content.match(/`([a-z][a-z0-9-]+)`/g) || [];
  for (const r of refs) {
    backtickRefs.push({ agent: f.replace(/\.md$/, ""), skill: r.replace(/`/g, "") });
  }
}
const knownSkillNames = new Set(skillDirs);
const agentNames = new Set(agentFiles.map((f) => f.replace(/\.md$/, "")));
const seen = new Set();
for (const { agent, skill } of backtickRefs) {
  const key = `${agent}->${skill}`;
  if (seen.has(key)) continue;
  seen.add(key);
  if (agentNames.has(skill)) continue;
  if (/^(https?|npm|npx|git|bash|json|yaml|yml|md|ts|js|tsx|jsx|css|html|env|csv|txt)$/.test(skill)) continue;
  if (/^(const|let|var|function|class|import|export|default|true|false|null|undefined|reflog)$/.test(skill)) continue;
  if (knownSkillNames.has(skill)) {
    summary.refs.ok++;
  } else {
    summary.refs.missing++;
    issues.push(`[REF] ${agent} menciona skill inexistente: \`${skill}\``);
  }
}

// ── 4. Cobertura de kits (kits.tsv) ──────────────────────────────
function readKits() {
  if (!fs.existsSync(KITS_FILE)) {
    issues.push(`[KITS] no existe ${path.relative(REPO, KITS_FILE)}`);
    return [];
  }
  return fs.readFileSync(KITS_FILE, "utf8")
    .split(/\r?\n/)
    .filter((l) => l.trim() && !l.startsWith("#"))
    .map((l) => {
      const p = l.split("\t");
      while (p.length < 4) p.push("");
      return {
        name: p[0],
        prefixes: p[1].split(",").filter(Boolean),
        excludes: p[2].split(",").filter(Boolean),
        names: p[3].split(",").filter(Boolean),
      };
    });
}
function kitMatches(kit, name) {
  if (kit.names.includes(name)) return true;
  return kit.prefixes.some((p) => {
    if (name !== p && !name.startsWith(p)) return false;
    return !kit.excludes.some((e) => name.startsWith(e));
  });
}
const kits = readKits();
summary.kits.kits = kits.length;
const covered = new Set();
for (const kit of kits) {
  let count = 0;
  for (const name of skillDirs) {
    if (kitMatches(kit, name)) {
      covered.add(name);
      count++;
    }
  }
  if (count === 0) issues.push(`[KITS] el kit "${kit.name}" no cubre ninguna skill`);
}
for (const name of skillDirs) {
  if (!covered.has(name)) {
    summary.kits.uncovered++;
    issues.push(`[KITS] la skill "${name}" no pertenece a ningún kit en kits.tsv`);
  }
}
for (const installer of ["install.sh", "install.ps1"]) {
  const p = path.join(REPO, installer);
  if (fs.existsSync(p) && !fs.readFileSync(p, "utf8").includes("kits.tsv")) {
    warnings.push(`[KITS] ${installer} no referencia kits.tsv`);
  }
}

// ── 5. Consistencia README (conteos y kits) ──────────────────────
if (fs.existsSync(README)) {
  const md = fs.readFileSync(README, "utf8");
  const skillsMatch = md.match(/\*\*(\d+)\s+skills\*\*/i);
  const agentsMatch = md.match(/\*\*(\d+)\s+agentes\*\*/i);
  if (skillsMatch && Number(skillsMatch[1]) !== skillDirs.length) {
    issues.push(`[README] declara ${skillsMatch[1]} skills, el repo tiene ${skillDirs.length}`);
  }
  if (agentsMatch && Number(agentsMatch[1]) !== agentFiles.length) {
    issues.push(`[README] declara ${agentsMatch[1]} agentes, el repo tiene ${agentFiles.length}`);
  }
  const kitsLine = md.match(/Kits disponibles:([^\n]+)/i);
  if (kitsLine) {
    for (const kit of kits) {
      if (!kitsLine[1].includes("`" + kit.name + "`")) {
        warnings.push(`[README] la lista de kits no menciona "${kit.name}"`);
      }
    }
  }
}

// ── 6-7. Consistencia repo vs instalación (solo modo completo) ───
function compareTree(repoDir, cfgDir, label) {
  if (!fs.existsSync(cfgDir)) {
    issues.push(`[SYNC] No existe ${cfgDir}`);
    return;
  }
  if (label === "skills") {
    const cfgDirs = listDirs(cfgDir);
    summary.skills.config = cfgDirs.length;
    for (const name of skillDirs) {
      const rDir = path.join(repoDir, name);
      const cDir = path.join(cfgDir, name);
      if (!fs.existsSync(path.join(cDir, "SKILL.md"))) {
        summary.skills.missing++;
        issues.push(`[SYNC] Skill no instalada en config: ${name}`);
        continue;
      }
      const diff = dirDiff(rDir, cDir);
      if (diff.length === 0) summary.skills.ok++;
      else {
        summary.skills.missing++;
        issues.push(`[SYNC] Skill distinta entre repo y config: ${name} -> ${diff.join(", ")}`);
      }
    }
  } else {
    const cfgFiles = fs.readdirSync(cfgDir).filter((f) => f.endsWith(".md"));
    summary.agents.config = cfgFiles.length;
    for (const f of agentFiles) {
      const r = path.join(repoDir, f);
      const c = path.join(cfgDir, f);
      if (!fs.existsSync(c)) {
        summary.agents.missing++;
        issues.push(`[SYNC] Agente no instalado en config: ${f}`);
      } else if (md5(r) === md5(c)) summary.agents.ok++;
      else {
        summary.agents.missing++;
        issues.push(`[SYNC] Agente distinto entre repo y config: ${f}`);
      }
    }
  }
}

if (!repoOnly) {
  compareTree(REPO_SKILLS, CFG_SKILLS, "skills");
  compareTree(REPO_AGENTS, CFG_AGENTS, "agents");

  const cfgAgentFiles = fs.existsSync(CFG_AGENTS)
    ? fs.readdirSync(CFG_AGENTS).filter((f) => f.endsWith(".md")).map((f) => f.replace(/\.md$/, ""))
    : [];
  for (const agent of BP_DELEGATES) {
    if (cfgAgentFiles.includes(agent)) summary.bp.ok++;
    else {
      summary.bp.missing++;
      issues.push(`[BP] business-planning delega a "${agent}" pero no está instalado en config`);
    }
  }
}

// ── Reporte ──────────────────────────────────────────────────────
const ok = issues.length === 0;
if (jsonFlag) {
  console.log(JSON.stringify({ mode: repoOnly ? "repo" : "full", config: CFG, summary, issues, warnings, ok }, null, 2));
  process.exit(ok ? 0 : 1);
}

console.log("=".repeat(62));
console.log("VERIFICACIÓN — opencode-skills");
console.log("=".repeat(62));
console.log(`Modo: ${repoOnly ? "solo repo (CI)" : "completo"}${repoOnly ? "" : ` | Config: ${CFG}`}`);
console.log("");
console.log("Skills:".padEnd(12), `repo=${summary.skills.repo}  auto-invocables=${summary.skills.auto} (${summary.skills.autoChars} chars)`);
console.log("Agentes:".padEnd(12), `repo=${summary.agents.repo}`);
console.log("Frontmatter:".padEnd(12), `válidos=${summary.frontmatter.ok}  con problemas=${summary.frontmatter.bad}`);
console.log("Refs skills:".padEnd(12), `existentes=${summary.refs.ok}  inexistentes=${summary.refs.missing}`);
console.log("Kits:".padEnd(12), `definidos=${summary.kits.kits}  sin kit=${summary.kits.uncovered}`);
if (!repoOnly) {
  console.log("Sync config:".padEnd(12), `skills ok=${summary.skills.ok} faltan=${summary.skills.missing} | agentes ok=${summary.agents.ok} faltan=${summary.agents.missing}`);
  console.log("Delegación BP:".padEnd(12), `agentes listos=${summary.bp.ok}  faltantes=${summary.bp.missing}`);
}
console.log("");

if (warnings.length) {
  console.log(`⚠️  ${warnings.length} advertencia(s):`);
  for (const w of warnings) console.log("  - " + w);
  console.log("");
}

if (ok) {
  console.log("✅ SIN HALLAZGOS.");
  process.exit(0);
} else {
  console.log(`❌ ${issues.length} hallazgo(s):`);
  for (const i of issues) console.log("  - " + i);
  process.exit(1);
}
