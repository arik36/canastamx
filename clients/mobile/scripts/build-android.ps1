param([switch]$ValidacionLocal, [switch]$ServidoresPublicos)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($ValidacionLocal.IsPresent -eq $ServidoresPublicos.IsPresent) { throw 'Elige un solo modo: -ValidacionLocal o -ServidoresPublicos.' }
$archivoApk = if ($ServidoresPublicos) { 'canastamx-servidores.apk' } else { 'canastamx-validacion.apk' }
if ((node -p "process.versions.node.split('.')[0]") -ne '20') { throw 'Activa Node 20.20.2 antes de generar el APK.' }
if ($PWD.Path.Length -gt 80) {
  # CMake/Ninja falla con las rutas largas del proyecto en Windows. Se compila
  # una copia nueva sin secretos; nunca se mueve ni borra el proyecto original.
  $origen = $PWD.Path
  $temporal = Join-Path ([System.IO.Path]::GetTempPath()) ('cmx215-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Path $temporal | Out-Null
  Get-ChildItem -LiteralPath $origen -Force | Where-Object {
    $_.Name -notin @('node_modules', 'android', 'ios', '.expo', 'artifacts', 'dist') -and $_.Name -notlike '.env*'
  } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $temporal $_.Name) -Recurse }
  Write-Output "Compilando una copia temporal sin secretos: $temporal"
  Push-Location -LiteralPath $temporal
  try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación en la copia temporal.' }
    & (Join-Path $temporal 'scripts/build-android.ps1') -ValidacionLocal:$ValidacionLocal -ServidoresPublicos:$ServidoresPublicos
    New-Item -ItemType Directory -Force (Join-Path $origen 'artifacts') | Out-Null
    Copy-Item -LiteralPath (Join-Path $temporal "artifacts/$archivoApk") -Destination (Join-Path $origen "artifacts/$archivoApk")
  } finally { Pop-Location }
  return
}
$env:EXPO_NO_DOTENV = '1'
if ($ServidoresPublicos) {
  $env:CANASTAMX_COMPILACION = 'entrega'
  $direcciones = Get-Content (Join-Path $PWD 'servidores-publicos.json') -Raw | ConvertFrom-Json
  $env:EXPO_PUBLIC_API_URL = $direcciones.dominio
  $env:EXPO_PUBLIC_ANALITICA_URL = $direcciones.analitica
  node scripts/verificar-build.cjs
  if ($LASTEXITCODE -ne 0) { throw 'Las direcciones públicas no son válidas.' }
} else {
  $env:CANASTAMX_COMPILACION = 'validacion'
  $env:EXPO_PUBLIC_API_URL = 'http://127.0.0.1:8084'
  $env:EXPO_PUBLIC_ANALITICA_URL = 'http://127.0.0.1:8004'
}
$env:NODE_OPTIONS = '--dns-result-order=ipv4first'
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
if (-not $env:JAVA_HOME) { throw 'Configura JAVA_HOME con un JDK 17 o 21 compatible con Gradle 9.0.' }
$env:PATH = "$env:JAVA_HOME/bin;$env:PATH"
node scripts/preparar-android.cjs
if ($LASTEXITCODE -ne 0) { throw 'Falló la preparación de las herramientas Android.' }
node node_modules/expo/bin/cli prebuild --platform android --no-install
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el proyecto Android.' }
Push-Location android
try {
  ./gradlew.bat assembleRelease --no-daemon '-PreactNativeArchitectures=arm64-v8a,x86_64'
  if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de Android.' }
} finally { Pop-Location }
New-Item -ItemType Directory -Force artifacts | Out-Null
Copy-Item -LiteralPath android/app/build/outputs/apk/release/app-release.apk -Destination "artifacts/$archivoApk"
Get-FileHash -Algorithm SHA256 "artifacts/$archivoApk"
Write-Output "APK: artifacts/$archivoApk. Firma de desarrollo; no acredita las pruebas de dos teléfonos ni sustituye la firma final de distribución."
