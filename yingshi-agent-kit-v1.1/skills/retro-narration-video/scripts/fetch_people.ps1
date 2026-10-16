# Fetch real historical figures by Commons CATEGORY (far more reliable than keyword search).
param(
  [string]$OutDir = "C:\Users\jonny\Documents\Codex\2026-10-05\context-md-brief-md-skill-references\work\porsche911\assets\source"
)
$ErrorActionPreference = "Continue"
$ua = "CodexStoryKit/1.0 (local documentary pilot)"
$head = @{ "User-Agent" = $ua }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$cats = @(
  @{ cat = "Category:Ferry Porsche";                 n = "person_ferry" },
  @{ cat = "Category:Ferdinand Porsche";             n = "person_ferdinand" },
  @{ cat = "Category:Ferdinand Alexander Porsche";   n = "person_butzi" },
  @{ cat = "Category:Enzo Ferrari";                  n = "person_enzo" }
)

$rows = @()
foreach ($item in $cats) {
  $c = [uri]::EscapeDataString($item.cat)
  $u = "https://commons.wikimedia.org/w/api.php?action=query&generator=categorymembers&gcmtitle=$c&gcmtype=file&gcmlimit=40&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1200&format=json"
  $picked = $null
  for ($a = 1; $a -le 3 -and -not $picked; $a++) {
    try {
      $r = Invoke-RestMethod -Uri $u -Headers $head -TimeoutSec 45
      $cands = @()
      foreach ($pg in $r.query.pages.PSObject.Properties.Value) {
        $ii = $pg.imageinfo[0]
        if (-not $ii) { continue }
        if ($ii.width -lt 300) { continue }
        $lic = $ii.extmetadata.LicenseShortName.value
        $rank = 9
        if ($lic -match 'Public domain|CC0|No restrictions') { $rank = 0 }
        elseif ($lic -match 'CC BY 2|CC BY 3|CC BY 4') { $rank = 1 }
        elseif ($lic -match 'CC BY-SA') { $rank = 2 }
        if ($rank -ge 9) { continue }
        $title = $pg.title
        $bonus = 0
        if ($title -match 'portrait|Portr|head|face|mug') { $bonus = -1 }
        $cands += [pscustomobject]@{ rank = ($rank + $bonus); title = $title; url = $ii.thumburl; lic = $lic; w = $ii.width }
      }
      if ($cands.Count -gt 0) {
        $picked = $cands | Sort-Object rank, @{Expression = { -$_.w }} | Select-Object -First 1
      }
    } catch {
      Start-Sleep -Seconds 5
    }
  }
  if (-not $picked) {
    Write-Host ("MISS {0}  ({1})" -f $item.n, $item.cat)
    Start-Sleep -Seconds 2
    continue
  }
  $out = Join-Path $OutDir "$($item.n).jpg"
  try {
    Invoke-WebRequest -Uri $picked.url -Headers $head -OutFile $out -TimeoutSec 150
    $rows += [pscustomobject]@{ name = $item.n; category = $item.cat; license = $picked.lic; title = $picked.title }
    Write-Host ("OK   {0,-18} {1,-12} {2}" -f $item.n, $picked.lic, $picked.title)
  } catch {
    Write-Host ("FAIL {0}" -f $item.n)
  }
  Start-Sleep -Seconds 3
}
$rows | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "_people_sources.json") -Encoding UTF8
Write-Host ("done {0}/{1}" -f $rows.Count, $cats.Count)
