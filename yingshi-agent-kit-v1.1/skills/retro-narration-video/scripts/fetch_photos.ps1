# Search Wikimedia Commons per topic, auto-pick one image (PD/CC0 first, then CC BY),
# download a 1600px thumbnail. ASCII-only: PowerShell 5.1 reads .ps1 as ANSI.
param(
  [string]$OutDir = "C:\Users\jonny\Documents\Codex\2026-10-05\context-md-brief-md-skill-references\work\porsche911\assets\source"
)
$ErrorActionPreference = "Continue"
$ua = "CodexYingshiKit/1.1 (local collage pilot)"
$head = @{ "User-Agent" = $ua }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$queries = @(
  @{ q = "Porsche 901 1963";                 n = "p901_1963" },
  @{ q = "Porsche 911 1965";                 n = "p911_1965" },
  @{ q = "Porsche 356";                      n = "p356" },
  @{ q = "Porsche 356 Speedster";            n = "p356_speedster" },
  @{ q = "Ferry Porsche";                    n = "ferry_porsche" },
  @{ q = "Ferdinand Alexander Porsche";      n = "butzi" },
  @{ q = "Volkswagen Beetle 1950s";          n = "beetle" },
  @{ q = "Porsche 911 Turbo 930";            n = "p930_turbo" },
  @{ q = "Porsche 964";                      n = "p964" },
  @{ q = "Porsche 993";                      n = "p993" },
  @{ q = "Porsche 996";                      n = "p996" },
  @{ q = "Porsche Boxster 1997";             n = "boxster" },
  @{ q = "Porsche Carrera GT";               n = "carrera_gt" },
  @{ q = "Porsche Panamera";                 n = "panamera" },
  @{ q = "Porsche 918 Spyder";               n = "p918" },
  @{ q = "Porsche 917 Le Mans";              n = "p917" },
  @{ q = "Porsche 956";                      n = "p956" },
  @{ q = "Porsche 919 Hybrid";               n = "p919" },
  @{ q = "Porsche 911 992";                  n = "p992" },
  @{ q = "Porsche Museum Stuttgart";         n = "museum" },
  @{ q = "Porsche factory Zuffenhausen";     n = "factory" },
  @{ q = "Le Mans circuit map";              n = "lemans_map" },
  @{ q = "Peugeot 404";                      n = "peugeot" },
  @{ q = "Porsche 911 GT3";                  n = "gt3" }
)

# License preference: Public domain / CC0 first, then CC BY, then CC BY-SA
function Get-LicRank($lic) {
  if ($lic -match 'Public domain|CC0|No restrictions') { return 0 }
  if ($lic -match 'CC BY 2|CC BY 3|CC BY 4') { return 1 }
  if ($lic -match 'CC BY-SA') { return 2 }
  return 9
}

$rows = @()
foreach ($item in $queries) {
  $e = [uri]::EscapeDataString($item.q)
  $u = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=$e&gsrlimit=8&gsrnamespace=6&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth=1600&format=json"
  $picked = $null
  for ($attempt = 1; $attempt -le 3 -and -not $picked; $attempt++) {
    try {
      $r = Invoke-RestMethod -Uri $u -Headers $head -TimeoutSec 60
      $cands = @()
      foreach ($pg in $r.query.pages.PSObject.Properties.Value) {
        $ii = $pg.imageinfo[0]
        if (-not $ii) { continue }
        if ($ii.width -lt 1200) { continue }
        $lic = $ii.extmetadata.LicenseShortName.value
        $rank = Get-LicRank $lic
        if ($rank -ge 9) { continue }
        $cands += [pscustomobject]@{ rank = $rank; title = $pg.title; url = $ii.thumburl; lic = $lic; w = $ii.width }
      }
      if ($cands.Count -gt 0) {
        $picked = ($cands | Sort-Object rank, @{Expression = { -$_.w }} | Select-Object -First 1)
      }
    } catch {
      Start-Sleep -Seconds 6
    }
  }
  if (-not $picked) {
    Write-Host ("MISS {0,-16} {1}" -f $item.n, $item.q)
    Start-Sleep -Seconds 3
    continue
  }
  $out = Join-Path $OutDir "$($item.n).jpg"
  try {
    Invoke-WebRequest -Uri $picked.url -Headers $head -OutFile $out -TimeoutSec 180
    $rows += [pscustomobject]@{ name = $item.n; query = $item.q; file = $out
      kb = [math]::Round((Get-Item $out).Length / 1KB); license = $picked.lic; title = $picked.title }
    Write-Host ("OK   {0,-16} {1,-10} {2}" -f $item.n, $picked.lic, $picked.title)
  } catch {
    Write-Host ("FAIL {0,-16} {1}" -f $item.n, $_.Exception.Message)
  }
  Start-Sleep -Seconds 3
}

$rows | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $OutDir "_sources.json") -Encoding UTF8
Write-Host ("done {0}/{1} images" -f $rows.Count, $queries.Count)
