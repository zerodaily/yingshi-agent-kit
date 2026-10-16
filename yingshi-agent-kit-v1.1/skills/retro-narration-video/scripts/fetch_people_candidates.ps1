# Fetch portrait CANDIDATES for real historical figures, with title filtering.
# Output goes to assets/people_candidates/<person>/NN_<file>.jpg so a labelled
# contact sheet can be reviewed before any photo is used in the film.
param(
  [string]$OutDir = "C:\Users\jonny\Documents\Codex\2026-10-05\context-md-brief-md-skill-references\work\porsche911\assets\people_candidates"
)
$ErrorActionPreference = "Continue"
$ua = "CodexStoryKit/1.0 (local documentary pilot)"
$head = @{ "User-Agent" = $ua }

# title must NOT contain these (houses, graves, cars, trains, signage ...)
$bad = 'Wohnhaus|house|Haus|Grab|grave|tomb|Denkmal|statue|Büste|bust|Zug|train|Bahnhof|Straße|street|Gebäude|building|Tafel|plaque|logo|sign|Wappen|coat of arms|Porsche 9|Porsche 3|356|911|917|956|959|924|944|968|Carrera|Turbo|Boxster|Cayenne|Panamera|Taycan|Volkswagen|Käfer|Beetle|Motor|engine|Fabrik|factory|Werk|Museum|Ingolstadt|Stuttgart|map|Karte|Skizze'

$cats = @(
  @{ cat = "Category:Ferry Porsche";               n = "ferry" },
  @{ cat = "Category:Ferdinand Porsche";           n = "ferdinand" },
  @{ cat = "Category:Ferdinand Alexander Porsche"; n = "butzi" },
  @{ cat = "Category:Enzo Ferrari (person)";       n = "enzo" }
)

foreach ($item in $cats) {
  $dir = Join-Path $OutDir $item.n
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $c = [uri]::EscapeDataString($item.cat)
  $u = "https://commons.wikimedia.org/w/api.php?action=query&generator=categorymembers&gcmtitle=$c&gcmtype=file&gcmlimit=60&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=900&format=json"
  try {
    $r = Invoke-RestMethod -Uri $u -Headers $head -TimeoutSec 45
  } catch {
    Write-Host ("MISS {0} (category not found)" -f $item.n); continue
  }
  $cands = @()
  foreach ($pg in $r.query.pages.PSObject.Properties.Value) {
    $ii = $pg.imageinfo[0]
    if (-not $ii) { continue }
    $title = $pg.title
    if ($title -match $bad) { continue }
    if ($title -notmatch '\.(jpg|jpeg|png)$') { continue }
    if ($ii.width -lt 350) { continue }
    $lic = $ii.extmetadata.LicenseShortName.value
    $ok = ($lic -match 'Public domain|CC0|No restrictions|CC BY')
    if (-not $ok) { continue }
    $surname = $item.n
    $score = 0
    if ($title -match 'portrait|Porträt|Photo|Foto|Bild|head|Kopf') { $score -= 2 }
    if ($title -match '19[2-9][0-9]|20[0-2][0-9]') { $score -= 1 }
    $cands += [pscustomobject]@{ score = $score; title = $title; url = $ii.thumburl; lic = $lic; w = $ii.width }
  }
  $picked = $cands | Sort-Object score, @{Expression = { -$_.w }} | Select-Object -First 6
  $i = 0
  $rows = @()
  foreach ($p in $picked) {
    $i++
    $safe = ($p.title -replace '^File:', '' -replace '[^A-Za-z0-9\.\-_]', '_')
    if ($safe.Length -gt 60) { $safe = $safe.Substring(0, 60) }
    $out = Join-Path $dir ("{0:D2}_{1}" -f $i, $safe)
    try {
      Invoke-WebRequest -Uri $p.url -Headers $head -OutFile $out -TimeoutSec 120
      $rows += [pscustomobject]@{ file = (Split-Path $out -Leaf); license = $p.lic; title = $p.title }
      Write-Host ("  {0} #{1} {2}" -f $item.n, $i, $p.title)
    } catch {
      Write-Host ("  {0} #{1} FAIL" -f $item.n, $i)
    }
    Start-Sleep -Seconds 2
  }
  if ($rows.Count -gt 0) {
    $rows | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $dir "_candidates.json") -Encoding UTF8
  }
}
Write-Host "done"
