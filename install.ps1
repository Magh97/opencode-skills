#Requires -Version 5.1
<#
.SYNOPSIS
    Instala los agentes y skills de opencode-skills en la configuracion global de opencode.
.DESCRIPTION
    Copia .opencode/agent/*.md a ~/.config/opencode/agent/ y, con -Global, las skills
    de skills/ a ~/.config/opencode/skills/ (solo si no estan ya instaladas por npx).
    Tambien soporta instalar solo agentes (-Agents) o solo skills (-Skills).
.EXAMPLE
    ./install.ps1
.EXAMPLE
    ./install.ps1 -Global
.EXAMPLE
    ./install.ps1 -Agents -Skills
.EXAMPLE
    # Solo instalar los kits de tu stack (skills + agentes)
    ./install.ps1 -Yes -Global -Kits dotnet,aspnet,sql-server,react,js,postgresql,flutter,git,planning,design,devops,agent,sputnik
.EXAMPLE
    # Instalar las skills tambien en los directorios universales de otros clientes
    ./install.ps1 -Yes -Global -Target opencode,agents,pi
#>
[CmdletBinding()]
param(
    [switch]$Global,
    [switch]$Agents,
    [switch]$Skills,
    [switch]$Yes,
    [string[]]$Kits,
    [switch]$ListKits,
    [string[]]$Target = @("opencode"),
    [switch]$ListTargets
)

$ErrorActionPreference = "Stop"

# Mapa de destino -> carpeta de skills. "opencode" es el destino de siempre;
# "agents" y "pi" son directorios universales que otros clientes de agentes
# (npx skills / Eve / PromptScript, y el cliente "pi") tambien leen.
$TargetMap = [ordered]@{
    "opencode" = (Join-Path $HOME ".config\opencode\skills")
    "agents"   = (Join-Path $HOME ".agents\skills")
    "pi"       = (Join-Path $HOME ".pi\agent\skills")
}

if ($ListTargets) {
    $TargetMap.Keys | ForEach-Object { Write-Host "$_ -> $($TargetMap[$_])" }
    exit 0
}

# Mapa de kit -> prefijo(s) de carpeta en skills/. "python" excluye "python-ai-intel-*"
# (que es su propio kit) y "security" agrupa las skills sueltas de seguridad que no
# comparten prefijo de carpeta.
$KitMap = [ordered]@{
    "agent"           = @{ Prefix = "agent-" }
    "aspnet"          = @{ Prefix = "aspnet-" }
    "design"          = @{ Prefix = "design-" }
    "devops"          = @{ Prefix = "devops-" }
    "dotnet"          = @{ Prefix = "dotnet-" }
    "flutter"         = @{ Prefix = "flutter-" }
    "git"             = @{ Prefix = "git-" }
    "js"              = @{ Prefix = "js-" }
    "nodejs"          = @{ Prefix = "nodejs-" }
    "planning"        = @{ Prefix = "planning-" }
    "ponytail"        = @{ Prefix = "ponytail" }
    "postgresql"      = @{ Prefix = "postgresql-" }
    "productivity"    = @{ Prefix = "productivity-" }
    "python-ai-intel" = @{ Prefix = "python-ai-intel-" }
    "python"          = @{ Prefix = "python-"; ExcludePrefix = "python-ai-intel-" }
    "react"           = @{ Prefix = "react-" }
    "security"        = @{ Names = @("application-security", "compliance-governance", "cryptography-secrets", "detection-response", "devsecops", "identity-access-management", "infrastructure-security", "secure-architecture", "security-fundamentals", "vulnerability-management") }
    "sputnik"         = @{ Prefix = "sputnik-" }
    "sql-server"      = @{ Prefix = "sql-server-" }
}

if ($ListKits) {
    $KitMap.Keys | Sort-Object | ForEach-Object { Write-Host $_ }
    exit 0
}

function Test-SkillInKits {
    param([string]$Name, [string[]]$SelectedKits)
    foreach ($kit in $SelectedKits) {
        if (-not $KitMap.Contains($kit)) {
            throw "Kit desconocido: '$kit'. Usa -ListKits para ver los kits disponibles."
        }
        $def = $KitMap[$kit]
        if ($def.Names) {
            if ($def.Names -contains $Name) { return $true }
        } else {
            if ($Name -eq $def.Prefix.TrimEnd('-') -or $Name.StartsWith($def.Prefix)) {
                if ($def.ExcludePrefix -and $Name.StartsWith($def.ExcludePrefix)) { continue }
                return $true
            }
        }
    }
    return $false
}

function Confirm-Action {
    param([string]$Message)
    if ($Yes) { return $true }
    $response = Read-Host "$Message (s/N)"
    return $response -match '^(s|y|si|yes)$'
}

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$configDir = Join-Path $HOME ".config\opencode"
$agentDir = Join-Path $configDir "agent"

# Kits y Target admiten comas dentro de un solo valor: -Kits dotnet,aspnet,react
if ($Kits) {
    $Kits = $Kits | ForEach-Object { $_ -split ',' } | Where-Object { $_ }
}
$Target = $Target | ForEach-Object { $_ -split ',' } | Where-Object { $_ }
foreach ($t in $Target) {
    if (-not $TargetMap.Contains($t)) {
        throw "Destino desconocido: '$t'. Usa -ListTargets para ver los destinos disponibles."
    }
}
$targetPaths = $Target | ForEach-Object { $TargetMap[$_] }

$doAgents = $Agents -or (-not $Skills)
$doSkills = $Skills -or (-not $Agents)

if ($doAgents) {
    $sourceAgents = Join-Path $repo ".opencode\agent"
    if (-not (Test-Path -LiteralPath $sourceAgents)) {
        throw "No se encontro $sourceAgents"
    }
    if (-not (Confirm-Action "Instalar $((Get-ChildItem $sourceAgents -Filter '*.md').Count) agentes en $agentDir ?")) {
        Write-Host "Instalacion de agentes cancelada."
        $doAgents = $false
    }
}

if ($doSkills -and $Global) {
    $sourceSkills = Join-Path $repo "skills"
    if (-not (Test-Path -LiteralPath $sourceSkills)) {
        throw "No se encontro $sourceSkills"
    }
    if (-not (Confirm-Action "Copiar skills a $($targetPaths -join ', ') ?")) {
        Write-Host "Instalacion de skills cancelada."
        $doSkills = $false
    }
} elseif ($doSkills -and -not $Global) {
    Write-Host "Para instalar skills use: npx skills add Magh97/opencode-skills --all"
    Write-Host "(o pase -Global para copiarlas manualmente a la carpeta global de opencode)"
    $doSkills = $false
}

if ($doAgents) {
    New-Item -ItemType Directory -Path $agentDir -Force | Out-Null
    Copy-Item -Path (Join-Path $sourceAgents "*.md") -Destination $agentDir -Force
    Write-Host "Agentes instalados en $agentDir"
    Write-Host "Agentes disponibles: $((Get-ChildItem $agentDir -Filter '*.md' -File).Name -join ', ')"
    if (Test-Path -LiteralPath (Join-Path $agentDir "build.md")) {
        Write-Host "Incluye build.md: override del agente build con reglas de orquestacion de subagentes."
    }
}

if ($doSkills) {
    $skillDirs = Get-ChildItem -Path $sourceSkills -Directory
    if ($Kits) {
        $skillDirs = $skillDirs | Where-Object { Test-SkillInKits -Name $_.Name -SelectedKits $Kits }
    }
    $total = (Get-ChildItem -Path $sourceSkills -Directory).Count
    foreach ($dest in $targetPaths) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
        $skillDirs | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        }
        Write-Host "Skills instaladas en $dest ($($skillDirs.Count) de $total)"
    }
}

Write-Host ""
Write-Host "Reinicia opencode para que los cambios tomen efecto."
