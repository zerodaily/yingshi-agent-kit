<#
  风格 B 合成：frames/ + BGM + 高潮冲击音 → MP4 1920x1080 30fps
  ──────────────────────────────────────────────────────────
  用法（在项目目录里，PowerShell）：
      powershell -ExecutionPolicy Bypass -File build.ps1
      powershell -ExecutionPolicy Bypass -File build.ps1 -Bgm "D:\music\千年之后.wav"
      powershell -ExecutionPolicy Bypass -File build.ps1 -Beat 17.048 -Out renders\final.mp4

  -Bgm  不填则用 assets\bgm.wav（Select-BGM.ps1 的产物）
  -Beat 必须与 film.html 的 CONFIG.beat 一致；换曲先实测重拍，别照抄
#>
param(
  [string]$Bgm = "",
  [double]$Beat = 17.0,
  [string]$Out = "renders\film.mp4",
  [double]$Volume = 0.85,
  [int]$Fps = 30
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath "frames\f0000.png")) {
  throw "frames\f0000.png 不存在，先跑 python render.py"
}

if (-not $Bgm) {
  if (Test-Path -LiteralPath "assets\bgm.wav") { $Bgm = (Resolve-Path "assets\bgm.wav").Path }
  else { throw "没有 BGM。用 -Bgm 指定音频文件，或把 BGM 放到 assets\bgm.wav" }
}
$Bgm = (Resolve-Path -LiteralPath $Bgm).Path

$html = Get-Content -LiteralPath "film.html" -Raw -Encoding UTF8
if ($html -match 'total\s*:\s*([0-9.]+)') {
  $total = [double]$Matches[1]
} else {
  throw "film.html 里读不到 CONFIG.total"
}

$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$tmp = Join-Path $PSScriptRoot ("_build_" + [guid]::NewGuid().ToString("N").Substring(0,8) + ".mp4")

$delayMs = [int]([math]::Round($Beat * 1000))
$fadeStart = [math]::Max(0, $total - 1.2)

$filter = "[2:a]adelay=${delayMs}|${delayMs}[boom];" `
        + "[1:a]atrim=0:${total},volume=${Volume},afade=t=out:st=${fadeStart}:d=1.2[mus];" `
        + "[mus][boom]amix=inputs=2:duration=first:dropout_transition=0[a]"

Write-Host "[build] total=${total}s beat=${Beat}s bgm=$Bgm"

& ffmpeg -y -framerate $Fps -i "frames\f%04d.png" -i $Bgm `
  -f lavfi -i "sine=frequency=72:duration=1.2,afade=t=out:st=0.05:d=1.15,volume=0.7" `
  -filter_complex $filter -map 0:v -map "[a]" `
  -c:v libx264 -pix_fmt yuv420p -r $Fps -c:a aac -b:a 192k -shortest $tmp
if ($LASTEXITCODE -ne 0) { throw "ffmpeg 失败（exit $LASTEXITCODE）" }

# 先写临时文件、校验通过再替换正式文件
& ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 $tmp | Out-Null
if ($LASTEXITCODE -ne 0) { throw "产物校验失败" }

Move-Item -LiteralPath $tmp -Destination $Out -Force
Write-Host "[build] 完成：$Out"
& ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_type,width,height,r_frame_rate -of default=noprint_wrappers=1 $Out
