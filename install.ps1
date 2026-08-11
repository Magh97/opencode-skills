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
#>
[CmdletBinding()]
param(
    [switch]$Global,
    [switch]$Agents,
    [switch]$Skills,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

function Confirm-Action {
    param([string]$Message)
    if ($Yes) { return $true }
    $response = Read-Host "$Message (s/N)"
    return $response -match '^(s|y|si|yes)$'
}

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$configDir = Join-Path $HOME ".config\opencode"
$agentDir = Join-Path $configDir "agent"
$skillDir = Join-Path $configDir "skills"

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
    if (-not (Confirm-Action "Copiar skills a $skillDir ?")) {
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
}

if ($doSkills) {
    New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
    Get-ChildItem -Path $sourceSkills -Directory | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $skillDir -Recurse -Force
    }
    Write-Host "Skills instaladas en $skillDir"
}

Write-Host ""
Write-Host "Reinicia opencode para que los cambios tomen efecto."
