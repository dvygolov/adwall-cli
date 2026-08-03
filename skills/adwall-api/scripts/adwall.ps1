param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AdWallArgs
)

$launcher = Join-Path $PSScriptRoot 'adwall.py'
python $launcher @AdWallArgs
exit $LASTEXITCODE
