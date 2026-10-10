#Requires -Version 5.1
<#
.SYNOPSIS
    Instala los agentes y skills de opencode-skills en la configuracion global de opencode.
.DESCRIPTION
    Copia .opencode/agent/*.md a ~/.config/opencode/agent/ y, con -Global, las skills
    de skills/ a ~/.config/opencode/skills/.
    Los kits se leen de .opencode/kits.tsv (fuente unica de verdad).
.EXAMPLE
    ./install.ps1
.EXAMPLE
    ./install.ps1 -Global
.EXAMPLE
    ./install.ps1 -Yes -Global -Kits dotnet,react,sql-server
.EXAMPLE
    ./install.ps1 -Yes -Global -Target opencode,agents,pi
.EXAMPLE
    ./install.ps1 -Yes -Global -DryRun
.EXAMPLE
    ./install.ps1 -Yes -Global -Prune
.EXAMPLE
    ./install.ps1 -Yes -Uninstall
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
    [switch]$ListTargets,
    [switch]$DryRun,
    [switch]$Prune,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$configDir = Join-Path $HOME ".config\opencode"
$agentDir = Join-Path $configDir "agent"
$kitFile = Join-Path $repo ".opencode\kits.tsv"

# Mapa de destino -> carpeta de skills. "opencode" es el destino de siempre;
# "agents" y "pi" son directorios universales que otros clientes tambien leen.
$TargetMap = [ordered]@{
    "opencode" = (Join-Path $HOME ".config\opencode\skills")
    "agents"   = (Join-Path $HOME ".agents\skills")
    "pi"       = (Join-Path $HOME ".pi\agent\skills")
}

if ($ListTargets) {
    $TargetMap.Keys | ForEach-Object { Write-Host "$_ -> $($TargetMap[$_])" }
    exit 0
}

if (-not (Test-Path -LiteralPath $kitFile)) {
    throw "No se encontro $kitFile (fuente de kits)."
}

# kits.tsv: kit<TAB>prefijos<TAB>prefijos-excluidos<TAB>nombres-exactos
$KitMap = [ordered]@{}
Get-Content -LiteralPath $kitFile | Where-Object { $_ -and -not $_.StartsWith("#") } | ForEach-Object {
    $parts = $_ -split "`t"
    while ($parts.Count -lt 4) { $parts += "" }
    $KitMap[$parts[0]] = @{
        Prefixes = @($parts[1] -split "," | Where-Object { $_ })
        Exclude  = @($parts[2] -split "," | Where-Object { $_ })
        Names    = @($parts[3] -split "," | Where-Object { $_ })
    }
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
        if ($def.Names -contains $Name) { return $true }
        foreach ($prefix in $def.Prefixes) {
            if ($Name -eq $prefix -or $Name.StartsWith($prefix)) {
                $skip = $false
                foreach ($ex in $def.Exclude) {
                    if ($Name.StartsWith($ex)) { $skip = $true }
                }
                if (-not $skip) { return $true }
            }
        }
    }
    return $false
}

function Confirm-Action {
    param([string]$Message)
    if ($Yes -or $DryRun) { return $true }
    $response = Read-Host "$Message (s/N)"
    return $response -match '^(s|y|si|yes)$'
}

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

# -Kits implica -Global: el filtro solo aplica a skills copiadas localmente
if ($Kits -and -not $Global) { $Global = $true }

# -Uninstall implica agentes + skills en modo global
if ($Uninstall) { $Global = $true; $Agents = $true; $Skills = $true }

$doAgents = $Agents -or (-not $Skills)
$doSkills = $Skills -or (-not $Agents)

if ($doAgents) {
    $sourceAgents = Join-Path $repo ".opencode\agent"
    if (-not (Test-Path -LiteralPath $sourceAgents)) {
        throw "No se encontro $sourceAgents"
    }
    $agentCount = (Get-ChildItem $sourceAgents -Filter '*.md' -File).Count
    if ($Uninstall) {
        if (Confirm-Action "Borrar $agentCount agentes instalados desde este repo en $agentDir?") {
            foreach ($f in Get-ChildItem $sourceAgents -Filter '*.md' -File) {
                $dest = Join-Path $agentDir $f.Name
                if ($DryRun) { Write-Host "[dry-run] rm $dest" }
                elseif (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force }
            }
            Write-Host "Agentes desinstalados de $agentDir"
        }
    } elseif (Confirm-Action "Instalar $agentCount agentes en $agentDir ?") {
        if ($DryRun) {
            Write-Host "[dry-run] crearia $agentDir y copiaria $agentCount agentes"
        } else {
            New-Item -ItemType Directory -Path $agentDir -Force | Out-Null
            Copy-Item -Path (Join-Path $sourceAgents "*.md") -Destination $agentDir -Force
            Write-Host "Agentes instalados en $agentDir"
            Write-Host "Agentes disponibles: $((Get-ChildItem $agentDir -Filter '*.md' -File).Name -join ', ')"
            if (Test-Path -LiteralPath (Join-Path $agentDir "build.md")) {
                Write-Host "Incluye build.md: override del agente build con reglas de orquestacion de subagentes."
            }
        }
    } else {
        Write-Host "Instalacion de agentes cancelada."
        $doAgents = $false
    }
}

if ($doSkills -and -not $Global -and -not $Uninstall) {
    Write-Host "Para instalar skills use: npx skills add Magh97/opencode-skills --all"
    Write-Host "(o pase -Global para copiarlas manualmente a la carpeta global de opencode)"
    $doSkills = $false
}

if ($doSkills) {
    $sourceSkills = Join-Path $repo "skills"
    if (-not (Test-Path -LiteralPath $sourceSkills)) {
        throw "No se encontro $sourceSkills"
    }
    $allDirs = Get-ChildItem -Path $sourceSkills -Directory
    $skillDirs = $allDirs
    if ($Kits) {
        $skillDirs = $skillDirs | Where-Object { Test-SkillInKits -Name $_.Name -SelectedKits $Kits }
    }
    $verb = "Copiar"
    if ($Uninstall) { $verb = "Borrar skills instaladas desde este repo de" }
    if (Confirm-Action "$verb $($targetPaths -join ', ') ?") {
        foreach ($dest in $targetPaths) {
            if ($Uninstall) {
                foreach ($skill in $skillDirs) {
                    $target = Join-Path $dest $skill.Name
                    if ($DryRun) { Write-Host "[dry-run] rm -rf $target" }
                    elseif (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
                }
                Write-Host "Skills desinstaladas de $dest ($($skillDirs.Count) de $($allDirs.Count))"
                continue
            }
            if (-not $DryRun) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
            foreach ($skill in $skillDirs) {
                if ($DryRun) { Write-Host "[dry-run] cp -r skills\$($skill.Name) -> $dest" }
                else { Copy-Item -Path $skill.FullName -Destination $dest -Recurse -Force }
            }
            Write-Host "Skills instaladas en $dest ($($skillDirs.Count) de $($allDirs.Count))"
            if ($Prune -and (Test-Path -LiteralPath $dest)) {
                foreach ($installed in Get-ChildItem -Path $dest -Directory) {
                    if (-not (Test-Path -LiteralPath (Join-Path $sourceSkills $installed.Name))) {
                        if ($DryRun) { Write-Host "[dry-run] prune $($installed.FullName)" }
                        else { Remove-Item -LiteralPath $installed.FullName -Recurse -Force; Write-Host "prune: $($installed.Name)" }
                    }
                }
            }
        }
    } else {
        Write-Host "Instalacion de skills cancelada."
        $doSkills = $false
    }
}

Write-Host ""
Write-Host "Reinicia opencode para que los cambios tomen efecto."
