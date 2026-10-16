# Fetch story-layer assets (people / places / event props) from Wikimedia Commons.
# ASCII only: PowerShell 5.1 reads .ps1 as ANSI, Chinese breaks string literals.
param(
  [string]$OutDir = "C:\Users\jonny\Documents\Codex\2026-10-05\context-md-brief-md-skill-references\work\porsche911\assets\source"
)
$ErrorActionPreference = "Continue"
$ua = "CodexStoryKit/1.0 (local documentary pilot)"
$head = @{ "User-Agent" = $ua }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$queries = @(
  @{ q = "Ferry Porsche";                      n = "ferry_porsche" },
  @{ q = "Ferdinand Alexander Porsche";        n = "butzi_designer" },
  @{ q = "Porsche 901";                        n = "p901_b" },
  @{ q = "Porsche factory 1960s";              n = "workshop" },
  @{ q = "Porsche 356 production";             n = "production" },
  @{ q = "International Motor Show Frankfurt"; n = "iaa" },
  @{ q = "Enzo Ferrari";                       n = "enzo" },
  @{ q = "car blueprint drawing";              n = "blueprint" },
  @{ q = "Porsche 911 engine bay";             n = "engine_bay" },
  @{ q = "Le Mans 1970 Porsche 917";           n = "lemans_1970" },
  @{ q = "Porsche family Ferry";               n = "porsche_family" },
  @{ q = "car dealership showroom 1960s";      n = "showroom" }
)

$rows = @()
foreach ($item in $queries) {
  $e = [uri]::EscapeDataString($item.q)
  $u = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=$e&gsrlimit=10&gsrnamespace=6&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1500&format=json"
  $picked = $null
  for ($attempt = 1; $attempt -le 3 -and -not $picked; $attempt++) {
    try {
      $r = Invoke-RestMethod -Uri $u -Headers $head -TimeoutSec 45
      $cands = @()
      foreach ($pg in $r.query.pages.PSObject.Properties.Value) {
        $ii = $pg.imageinfo[0]
        if (-not $ii) { continue }
        if ($ii.width -lt 800) { continue }
        $lic = $ii.extmetadata.LicenseShortName.value
        $rank = 9
        if ($lic -match 'Public domain|CC0|No restrictions') { $rank = 0 }
        elseif ($lic -match 'CC BY 2|CC BY 3|CC BY 4') { $rank = 1 }
        elseif ($lic -match 'CC BY-SA') { $rank = 2 }
        if ($rank -ge 9) { continue }
        $cands += [pscustomobject]@{ rank = $rank; title = $pg.title; url = $ii.thumburl; lic = $lic; w = $ii.width }
      }
      if ($cands.Count -gt 0) {
        $picked = $cands | Sort-Object rank, @{Expression = { -$_.w }} | Select-Object -First 1
      }
    } catch {
      Start-Sleep -Seconds 5
    }
  }
  if (-not $picked) {
    Write-Host ("MISS {0}" -f $item.n)
    Start-Sleep -Seconds 2
    continue
  }
  $out = Join-Path $OutDir "$($item.n).jpg"
  try {
    Invoke-WebRequest -Uri $picked.url -Headers $head -OutFile $out -TimeoutSec 150
    $rows += [pscustomobject]@{ name = $item.n; query = $item.q; license = $picked.lic; title = $picked.title }
    Write-Host ("OK   {0,-16} {1,-12} {2}" -f $item.n, $picked.lic, $picked.title)
  } catch {
    Write-Host ("FAIL {0}" -f $item.n)
  }
  Start-Sleep -Seconds 3
}
$rows | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "_story_sources.json") -Encoding UTF8
Write-Host ("done {0}/{1}" -f $rows.Count, $queries.Count)
