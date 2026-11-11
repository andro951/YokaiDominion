param([string]$GodotPath = $env:GODOT_BIN)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$game = Join-Path $root 'game'
if (-not (Test-Path (Join-Path $game 'Assets/Character01/character-blockout.glb'))) {
    throw 'Character asset is missing. Install the character-blockout Actions artifact with tools/install_character_asset.py, or use the milestone bundle with assets already included.'
}
if (-not $GodotPath) {
    $command = Get-Command godot -ErrorAction SilentlyContinue
    if ($command) { $GodotPath = $command.Source }
}
if (-not $GodotPath -or -not (Test-Path $GodotPath)) {
    throw 'Pass -GodotPath pointing to the Godot 4.7.2 .NET executable, or set GODOT_BIN.'
}
$version = (& $GodotPath --version | Select-Object -First 1)
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^4\.7\.2\..*mono') {
    throw "Expected Godot 4.7.2 .NET; got: $version"
}
Push-Location $root
try {
    # Optimize the numerical reference runtime even when loading the editor's Debug assembly.
    & dotnet build game/YokaiDominion.csproj -c Debug -p:Optimize=true
    if ($LASTEXITCODE -ne 0) { throw 'C# build failed. Install the .NET 10 SDK and inspect the output above.' }
    & $GodotPath --headless --editor --path $game --import
    if ($LASTEXITCODE -ne 0) { throw 'Godot asset import failed.' }
    & $GodotPath --path $game res://Scenes/CharacterLab.tscn
    if ($LASTEXITCODE -ne 0) { throw 'The character laboratory reported an error.' }
} finally {
    Pop-Location
}
