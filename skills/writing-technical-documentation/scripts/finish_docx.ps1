<#
.SYNOPSIS
Finish a pandoc-exported .docx in Microsoft Word on Windows: fill the contents list, fix table layout, save.

.DESCRIPTION
Pandoc writes the Word contents list as an empty field that fills in only when Word updates it, and it
leaves tables on autofit, so rows split across pages and header rows can sit alone at a page bottom.
This script opens the file in Word through COM, without showing Word, and:

  - sets fixed table widths: from a JSON width map when one matches, otherwise from cell text lengths
  - keeps each table row on one page, repeats the header row on every page, and keeps it with the next row
  - gives contents levels 1 and 2 hanging indents and right-aligned, dot-leader page numbers, so "5.10" lines up
  - fills the contents list and its page numbers, then saves, and optionally writes a PDF

Word runs in a background job with a time limit. Afterwards the script stops only Word processes that
started during the run, so a document the user has open in Word is left alone.

Width map: a JSON object whose keys are "first header|second header|columns" or "first header|columns"
and whose values are column percentages, for example {"Setting|4": [27, 20, 23, 30]}.

Exit codes:
  0  finished
  1  Word reported an error; the message is printed
  2  bad arguments, file not found, or Word is not installed
  3  Word did not finish within -TimeoutSec; new Word processes were stopped
  4  the file is locked, usually because it is open in Word; close it or export to another path

Examples:
  powershell -NoProfile -File finish_docx.ps1 -Docx build\design.docx
  powershell -NoProfile -File finish_docx.ps1 -Docx build\design.docx -Pdf build\design.pdf
  powershell -NoProfile -File finish_docx.ps1 -Docx build\design.docx -Widths docs\pandoc\widths.json -TimeoutSec 300
#>
param(
  [string]$Docx,
  [string]$Pdf,
  [string]$Widths,
  [int]$TimeoutSec = 180,
  [switch]$Help
)

if ($Help -or -not $Docx) { Get-Help $PSCommandPath -Detailed; exit $(if ($Help) { 0 } else { 2 }) }
if (-not (Test-Path -LiteralPath $Docx -PathType Leaf)) { "error: not found: $Docx"; exit 2 }
$Docx = (Resolve-Path -LiteralPath $Docx).Path
if ($Pdf) { $Pdf = [IO.Path]::GetFullPath($Pdf) }
try { [void][Type]::GetTypeFromProgID('Word.Application', $true) } catch { "error: Microsoft Word is not installed"; exit 2 }

$map = @{}
if ($Widths) {
  if (-not (Test-Path -LiteralPath $Widths -PathType Leaf)) { "error: width map not found: $Widths"; exit 2 }
  try {
    $json = Get-Content -LiteralPath $Widths -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $json.PSObject.Properties) { $map[$p.Name] = @($p.Value | ForEach-Object { [double]$_ }) }
  } catch { "error: width map is not valid JSON: $_"; exit 2 }
}

# A file open in Word cannot be saved over. Fail early with a clear message instead of a COM error.
try { $fs = [IO.File]::Open($Docx, 'Open', 'ReadWrite', 'None'); $fs.Close() }
catch { "error: $Docx is locked, probably open in Word. Close it, or export to another path and copy later."; exit 4 }

$before = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })

$job = Start-Job -ArgumentList $Docx, $Pdf, $map -ScriptBlock {
  param($Docx, $Pdf, $map)
  $w = New-Object -ComObject Word.Application
  $w.Visible = $false; $w.DisplayAlerts = 0
  try {
    $d = $w.Documents.Open($Docx, $false, $false, $false)
    $usable = $d.PageSetup.PageWidth - $d.PageSetup.LeftMargin - $d.PageSetup.RightMargin
    $auto = 0; $mapped = 0
    foreach ($t in $d.Tables) {
      $cols = $t.Columns.Count
      $h1 = ($t.Cell(1, 1).Range.Text -replace "[`r`a]", '').Trim()
      $h2 = if ($cols -gt 1) { ($t.Cell(1, 2).Range.Text -replace "[`r`a]", '').Trim() } else { '' }
      $pct = $map["$h1|$h2|$cols"]; if (-not $pct) { $pct = $map["$h1|$cols"] }
      if ($pct -and $pct.Count -eq $cols) { $mapped++ } else {
        # Each column first gets room for its longest word (capped, so a long path wraps), measured in
        # points at about 5.5 pt a character plus cell padding. Spare width then goes to the columns
        # whose average text is longer than that minimum, so prose columns grow and short ones stay narrow.
        $auto++
        $rows = [Math]::Min($t.Rows.Count, 40)
        $minPt = @(); $extra = @()
        for ($c = 1; $c -le $cols; $c++) {
          $sum = 0; $n = 0; $longestWord = 3
          for ($r = 1; $r -le $rows; $r++) {
            try { $txt = ($t.Cell($r, $c).Range.Text -replace "[`r`a]", '').Trim() } catch { continue }
            foreach ($word in $txt -split '\s+') { $longestWord = [Math]::Max($longestWord, $word.Length) }
            if ($r -gt 1 -or $rows -eq 1) { $sum += [Math]::Min($txt.Length, 300); $n++ }
          }
          $longestWord = [Math]::Min($longestWord, 16)
          $minPt += $longestWord * 5.5 + 12
          $extra += [Math]::Max($sum / [Math]::Max($n, 1) - $longestWord, 0)
        }
        $minTotal = ($minPt | Measure-Object -Sum).Sum
        $extraTotal = ($extra | Measure-Object -Sum).Sum
        $spare = $usable - $minTotal
        $pts = @()
        for ($c = 0; $c -lt $cols; $c++) {
          if ($spare -le 0) { $pts += $usable * $minPt[$c] / $minTotal }
          elseif ($extraTotal -gt 0) { $pts += $minPt[$c] + $spare * $extra[$c] / $extraTotal }
          else { $pts += $minPt[$c] + $spare / $cols }
        }
        $pct = @($pts | ForEach-Object { 100 * $_ / $usable })
      }
      $t.AllowAutoFit = $false
      $t.PreferredWidthType = 3; $t.PreferredWidth = $usable
      for ($c = 1; $c -le $cols; $c++) { try { $t.Columns.Item($c).Width = $usable * $pct[$c - 1] / 100 } catch {} }
      $t.Rows.AllowBreakAcrossPages = $false
      $t.Rows.Item(1).HeadingFormat = $true
      $t.Rows.Item(1).Range.ParagraphFormat.KeepWithNext = $true
    }
    try { [void]$d.Styles.Item('Heading 2').ParagraphFormat.TabStops.Add(46) } catch {}
    # Contents: number at the margin (level 1) or 11 pt in (level 2), text after a hanging indent,
    # page number right-aligned with a dot leader. Word treats the hanging indent as the first tab stop.
    foreach ($lvl in @(@('TOC 1', 24, -24), @('TOC 2', 50, -39))) {
      try {
        $pf = $d.Styles.Item($lvl[0]).ParagraphFormat
        $pf.TabStops.ClearAll(); $pf.LeftIndent = $lvl[1]; $pf.FirstLineIndent = $lvl[2]
        [void]$pf.TabStops.Add($usable, 2, 1)
      } catch {}
    }
    foreach ($toc in $d.TablesOfContents) { $toc.Update() }
    $d.Repaginate()
    foreach ($toc in $d.TablesOfContents) { $toc.UpdatePageNumbers() }
    "tables: $($d.Tables.Count) ($mapped from width map, $auto sized from text); contents lists: $($d.TablesOfContents.Count); pages: $($d.ComputeStatistics(2))"
    $d.Save()
    if ($Pdf) { $d.ExportAsFixedFormat($Pdf, 17); "pdf: $Pdf" }
    $d.Close([ref]0)
    "ok"
  } catch {
    # RPC_E_DISCONNECTED after a successful save is harmless: Word has already written the file.
    if ("$_" -match '0x80010108') { "ok (Word disconnected after saving)" } else { "error: $_" }
  } finally { try { $w.Quit([ref]0) } catch {} }
}

$done = Wait-Job $job -Timeout $TimeoutSec
$out = @(Receive-Job $job -ErrorAction SilentlyContinue)
Remove-Job $job -Force
Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Id } | Stop-Process -Force -ErrorAction SilentlyContinue

$out | ForEach-Object { $_ }
if (-not $done) { "error: Word did not finish within $TimeoutSec seconds"; exit 3 }
if ($out -match '^ok') { exit 0 }
exit 1
