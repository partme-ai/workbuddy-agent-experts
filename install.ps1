# Install the pre-built WorkBuddy expert teams (Windows).
# Requires Python 3 (py launcher or python on PATH).
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$py = Get-Command python -ErrorAction SilentlyContinue
$extra = @()
if (-not $py) {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { $extra = @("-3") } else {
    Write-Error "Python 3 not found. Install it from https://www.python.org/downloads/ first."
  }
}
& $py.Source @extra (Join-Path $PSScriptRoot "scripts\install.py") @args
exit $LASTEXITCODE
