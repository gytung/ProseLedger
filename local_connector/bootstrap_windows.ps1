$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'A 64-bit Windows computer is required.' }
    $python = Join-Path $PSScriptRoot 'runtime\python\python.exe'
    $candidates = @($python, (Join-Path (Split-Path $PSScriptRoot) 'runtime\windows\python\python.exe'))
    foreach ($commandName in @('python.exe', 'python3.exe')) {
        $candidate = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($candidate -and $candidate.Source -notmatch 'WindowsApps') { $candidates += $candidate.Source }
    }
    $found = $null
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            & $candidate -c 'import sys, ssl, ctypes, urllib.request, tarfile, zipfile, http.server; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { $found = $candidate; break }
        }
    }
    if (-not $found) {
        Write-Host 'Preparing a private Python runtime (11 MB, first launch only)...'
        $directory = Split-Path $python
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
        $archive = Join-Path $PSScriptRoot 'runtime\python.zip'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $archive
        $expected = '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3'
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant() -ne $expected) { throw 'Python download fingerprint mismatch. Start again.' }
        Expand-Archive -LiteralPath $archive -DestinationPath $directory -Force
        # Embedded Python uses an explicit, private search path. Add only this connector's folder.
        Set-Content -LiteralPath (Join-Path $directory 'python312._pth') -Encoding ASCII -Value @('python312.zip', '.', '..\..')
        Remove-Item -LiteralPath $archive
        $found = $python
    }
    & $found (Join-Path $PSScriptRoot 'start.py')
    if ($LASTEXITCODE -ne 0) { throw 'The connector stopped. Read the explanation above, then try again.' }
} catch {
    Write-Host ('Unable to start: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
