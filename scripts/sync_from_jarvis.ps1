<#
  Sincroniza el código de Alpha50 desde Jarvis (fuente de verdad) a este repo.

  Alpha50 se desarrolla dentro de Jarvis (alpha50/ + connectors/garmin_workouts.py).
  Este repo es su escaparate independiente: aquí solo se copia CÓDIGO.
  Los datos personales (alpha50_cronologia.db, alpha50_plan.json, .garmin_session,
  .env) NO se copian nunca.

  Uso (PowerShell, desde la raíz de este repo):
      .\scripts\sync_from_jarvis.ps1
      .\scripts\sync_from_jarvis.ps1 -JarvisDir D:\otra\ruta\jarvis
  Después: revisar `git diff`, commit y push.
#>
param(
    [string]$JarvisDir = "C:\Users\Usuario\jarvis"
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$JarvisDir\alpha50\scheduler.py")) {
    throw "No encuentro $JarvisDir\alpha50\scheduler.py -- revisa -JarvisDir"
}

# 1. Código Alpha50 (solo .py; sin backups)
Get-ChildItem "$JarvisDir\alpha50\*.py" |
    Where-Object { $_.Name -notlike "*_backup_*" } |
    ForEach-Object {
        Copy-Item $_.FullName "$Repo\alpha50\$($_.Name)" -Force
        Write-Host "  alpha50\$($_.Name)"
    }

# 2. Conector que sube los workouts al reloj
Copy-Item "$JarvisDir\connectors\garmin_workouts.py" "$Repo\connectors\garmin_workouts.py" -Force
Write-Host "  connectors\garmin_workouts.py"

# 3. Comprobación de seguridad: nada de datos personales en el árbol
$prohibidos = Get-ChildItem $Repo -Recurse -File -Include *.db, *.env, alpha50_plan.json -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "*\.git\*" }
if ($prohibidos) {
    Write-Warning "Hay ficheros de datos en el repo (están en .gitignore, pero revisa):"
    $prohibidos | ForEach-Object { Write-Warning "  $($_.FullName)" }
}

# 4. Tests
Push-Location $Repo
try {
    python -m unittest discover -s tests
    git status --short
} finally {
    Pop-Location
}
