# Bundle Size Verification Script
Write-Host "=== Bundle Size Verification ===" -ForegroundColor Cyan
Write-Host ""

# Get file sizes
$cssFiles = Get-ChildItem -Path "dist/css" -Filter "*.css" -Recurse
$jsFiles = Get-ChildItem -Path "dist/js" -Filter "*.js" -Recurse -Exclude "*.map"
$htmlFiles = Get-ChildItem -Path "dist" -Filter "*.html"
$libFiles = Get-ChildItem -Path "dist/lib" -Filter "*.js" -Recurse

# Calculate sizes
$totalCssSize = ($cssFiles | Measure-Object -Property Length -Sum).Sum
$totalJsSize = ($jsFiles | Measure-Object -Property Length -Sum).Sum
$totalHtmlSize = ($htmlFiles | Measure-Object -Property Length -Sum).Sum
$totalLibSize = ($libFiles | Measure-Object -Property Length -Sum).Sum
$totalSize = $totalCssSize + $totalJsSize + $totalHtmlSize + $totalLibSize

# Display individual file sizes
Write-Host "CSS Files:" -ForegroundColor Yellow
foreach ($file in $cssFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  $($file.Name): $sizeKB KB"
}

Write-Host ""
Write-Host "JavaScript Files:" -ForegroundColor Yellow
foreach ($file in $jsFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  $($file.Name): $sizeKB KB"
}

Write-Host ""
Write-Host "Library Files:" -ForegroundColor Yellow
foreach ($file in $libFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  $($file.Name): $sizeKB KB"
}

Write-Host ""
Write-Host "HTML Files:" -ForegroundColor Yellow
foreach ($file in $htmlFiles) {
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    Write-Host "  $($file.Name): $sizeKB KB"
}

# Display totals
Write-Host ""
Write-Host "=== Totals ===" -ForegroundColor Cyan
Write-Host "Total CSS: $([math]::Round($totalCssSize / 1KB, 2)) KB"
Write-Host "Total JS (app): $([math]::Round($totalJsSize / 1KB, 2)) KB"
Write-Host "Total JS (lib): $([math]::Round($totalLibSize / 1KB, 2)) KB"
Write-Host "Total HTML: $([math]::Round($totalHtmlSize / 1KB, 2)) KB"
Write-Host "Total Bundle: $([math]::Round($totalSize / 1KB, 2)) KB"
Write-Host ""

# Check against requirements
Write-Host "=== Requirements Check ===" -ForegroundColor Cyan
$cssLimit = 50
$jsLimit = 100
$totalLimit = 500

$cssSizeKB = [math]::Round($totalCssSize / 1KB, 2)
$jsSizeKB = [math]::Round($totalJsSize / 1KB, 2)
$totalSizeKB = [math]::Round($totalSize / 1KB, 2)

if ($cssSizeKB -lt $cssLimit) {
    Write-Host "✓ CSS size ($cssSizeKB KB) is under $cssLimit KB limit" -ForegroundColor Green
} else {
    Write-Host "✗ CSS size ($cssSizeKB KB) exceeds $cssLimit KB limit" -ForegroundColor Red
}

if ($jsSizeKB -lt $jsLimit) {
    Write-Host "✓ App JS size ($jsSizeKB KB) is under $jsLimit KB limit" -ForegroundColor Green
} else {
    Write-Host "✗ App JS size ($jsSizeKB KB) exceeds $jsLimit KB limit" -ForegroundColor Red
}

if ($totalSizeKB -lt $totalLimit) {
    Write-Host "✓ Total bundle size ($totalSizeKB KB) is under $totalLimit KB limit" -ForegroundColor Green
} else {
    Write-Host "✗ Total bundle size ($totalSizeKB KB) exceeds $totalLimit KB limit" -ForegroundColor Red
}

Write-Host ""
Write-Host "Note: These are uncompressed sizes. With gzip compression, sizes will be ~70% smaller." -ForegroundColor Yellow
Write-Host "Estimated gzipped total: $([math]::Round($totalSizeKB * 0.3, 2)) KB" -ForegroundColor Yellow
