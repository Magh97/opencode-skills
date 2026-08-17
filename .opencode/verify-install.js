#!/usr/bin/env node
/**
 * Verificación de instalación de opencode-skills
 * 
 * Valida:
 *  1. Frontmatter YAML de todas las skills (name + description obligatorios)
 *  2. Frontmatter de todos los agentes (description + mode válido)
 *  3. Referencias cruzadas: skills mencionadas en agentes existen en skills/
 *  4. Consistencia repo vs instalación (~/.config/opencode) por hash MD5
 *  5. Que los agentes referenciados por business-planning existan
 *
 * Uso: node verify-install.js [--fix-report]
 * Salida: tabla resumen + códigos de salida (0 ok, 1 con hallazgos)
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const YAML = require("yaml");

// ── Configuración ────────────────────────────────────────────────
const REPO = __dirname; // .opencode/
const REPO_SKILLS = path.join(REPO, "..", "skills");
const REPO_AGENTS = path.join(REPO, "agent");
const CFG = path.join(require("os").homedir(), ".config", "opencode");
const CFG_SKILLS = path.join(CFG, "skills");
const CFG_AGENTS = path.join(CFG, "agent");

const VALID_MODES = ["primary", "all", "subagent"];

// Agentes que business-planning delega vía task
const BP_DELEGATES = ["planning", "design", "docs"];

const issues = [];
const summary = {
  skills: { repo: 0, config: 0, ok: 0, missing: 0 },
  agents: { repo: 0, config: 0, ok: 0, missing: 0 },
  frontmatter: { ok: 0, bad: 0 },
  refs: { ok: 0, missing: 0 },
  bp: { ok: 0, missing: 0 },
};

function md5(file) {
  return crypto.createHash("md5").update(fs.readFileSync(file)).digest("hex");
}

function parseFrontmatter(file) {
  const content = fs.readFileSync(file, "utf8");
  if (!content.startsWith("---")) return { error: "no frontmatter (no empieza con ---)" };
  const end = content.indexOf("\n---", 3);
  if (end === -1) return { error: "frontmatter sin cierre (---)" };
  const raw = content.slice(3, end).replace(/\r/g, ""); // normalizar CRLF → LF
  // Parseo por líneas: formato frontmatter simple de este repo.
  // NO usar YAML.parse estricto: las descriptions contienen ":" dentro de comillas
  // que la librería yaml rechaza (aunque opencode las acepta).
  const fm = {};
  const lines = raw.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(/^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$/);
    if (m) {
      let val = m[2].trim();
      // Descripción en bloque plegado (description: > ...) — unir líneas indentadas siguientes
      if (val === ">") {
        const block = [];
        let j = i + 1;
        while (j < lines.length && lines[j].startsWith("  ")) {
          block.push(lines[j].trim());
          j++;
        }
        val = block.join(" ");
        i = j - 1;
      }
      // quitar comillas envolventes simples o dobles
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      fm[m[1]] = val;
    }
  }
  return { fm, error: fm.name === undefined && fm.description === undefined ? "frontmatter vacío o sin campos reconocibles" : null };
}

function listDirs(dir) {
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && fs.existsSync(path.join(dir, d.name, "SKILL.md")))
    .map((d) => d.name);
}

// ── 1. Frontmatter de skills ─────────────────────────────────────
const skillDirs = listDirs(REPO_SKILLS);
summary.skills.repo = skillDirs.length;
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
  summary.frontmatter.ok++;
}

// ── 2. Frontmatter de agentes ────────────────────────────────────
const agentFiles = fs.readdirSync(REPO_AGENTS).filter((f) => f.endsWith(".md"));
summary.agents.repo = agentFiles.length;
for (const f of agentFiles) {
  const file = path.join(REPO_AGENTS, f);
  const { fm, error } = parseFrontmatter(file);
  const agentName = f.replace(/\.md$/, "");
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
    const name = r.replace(/`/g, "");
    backtickRefs.push({ agent: f.replace(/\.md$/, ""), skill: name });
  }
}
// Solo validamos refs que parecen skills (excluyen agentes, comandos, formatos)
const knownSkillNames = new Set(skillDirs);
// Nombres de agentes (aparecen en backticks en secciones de delegación) NO son skills
const agentNames = new Set(agentFiles.map((f) => f.replace(/\.md$/, "")));
const seen = new Set();
for (const { agent, skill } of backtickRefs) {
  const key = `${agent}->${skill}`;
  if (seen.has(key)) continue;
  seen.add(key);
  // Excluir: agentes, formatos, comandos y términos comunes de código
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

// ── 4. Consistencia repo vs instalación ──────────────────────────
function compareTree(repoDir, cfgDir, label) {
  if (!fs.existsSync(cfgDir)) {
    issues.push(`[SYNC] No existe ${cfgDir}`);
    return;
  }
  if (label === "skills") {
    const cfgDirs = listDirs(cfgDir);
    summary.skills.config = cfgDirs.length;
    for (const name of skillDirs) {
      const r = path.join(repoDir, name, "SKILL.md");
      const c = path.join(cfgDir, name, "SKILL.md");
      if (!fs.existsSync(c)) {
        summary.skills.missing++;
        issues.push(`[SYNC] Skill no instalada en config: ${name}`);
      } else if (md5(r) === md5(c)) {
        summary.skills.ok++;
      } else {
        summary.skills.missing++;
        issues.push(`[SYNC] Skill distinta entre repo y config: ${name}`);
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
      } else if (md5(r) === md5(c)) {
        summary.agents.ok++;
      } else {
        summary.agents.missing++;
        issues.push(`[SYNC] Agente distinto entre repo y config: ${f}`);
      }
    }
  }
}
compareTree(REPO_SKILLS, CFG_SKILLS, "skills");
compareTree(REPO_AGENTS, CFG_AGENTS, "agents");

// ── 5. Delegaciones de business-planning ─────────────────────────
const cfgAgentFiles = fs.existsSync(CFG_AGENTS)
  ? fs.readdirSync(CFG_AGENTS).filter((f) => f.endsWith(".md")).map((f) => f.replace(/\.md$/, ""))
  : [];
for (const agent of BP_DELEGATES) {
  if (cfgAgentFiles.includes(agent)) {
    summary.bp.ok++;
  } else {
    summary.bp.missing++;
    issues.push(`[BP] business-planning delega a "${agent}" pero no está instalado en config`);
  }
}

// ── Reporte ──────────────────────────────────────────────────────
console.log("=".repeat(62));
console.log("VERIFICACIÓN DE INSTALACIÓN — opencode-skills");
console.log("=".repeat(62));
console.log("");
console.log("Skills:".padEnd(10), `repo=${summary.skills.repo}  config=${summary.skills.config}  idénticas=${summary.skills.ok}  con diferencias/faltantes=${summary.skills.missing}`);
console.log("Agentes:".padEnd(10), `repo=${summary.agents.repo}  config=${summary.agents.config}  idénticos=${summary.agents.ok}  con diferencias/faltantes=${summary.agents.missing}`);
console.log("Frontmatter:".padEnd(10), `válidos=${summary.frontmatter.ok}  con problemas=${summary.frontmatter.bad}`);
console.log("Refs de skills:".padEnd(10), `existentes=${summary.refs.ok}  inexistentes=${summary.refs.missing}`);
console.log("Delegación BP:".padEnd(10), `agentes listos=${summary.bp.ok}  faltantes=${summary.bp.missing}`);
console.log("");

if (issues.length === 0) {
  console.log("✅ INSTALACIÓN VERIFICADA: sin hallazgos.");
  process.exit(0);
} else {
  console.log(`⚠️  ${issues.length} hallazgo(s):`);
  for (const i of issues) console.log("  - " + i);
  process.exit(1);
}
