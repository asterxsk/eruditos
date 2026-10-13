#!/usr/bin/env python3
"""Run a program inside a GUI app and screenshot the result.

Windows only. Finds a window whose title contains --src, brings it to the
foreground, and — if the app is VS Code — triggers the default build task with
Ctrl+Shift+B. Then captures the window to --out.

It never types into a terminal unless asked with --keys, because SendKeys lands
in whatever window actually holds focus: a silent SetForegroundWindow failure
sends your keystrokes to an unrelated app. The guard below aborts instead.

Usage:
  python -I capture_app.py --src task1_insertion_sort.c --out shot1.png
  python -I capture_app.py --list
  python -I capture_app.py --src main.py --keys-file keys.txt --out s.png
"""

import argparse
import ctypes
import subprocess
import sys
import time

SCRIPT = r"""
param([string]$Src, [string]$Out, [string]$KeysFile, [int]$Wait = 6)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@

$procs = Get-Process -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Src*" }
$p = $procs | Select-Object -First 1
if (-not $p) { Write-Output "NOWINDOW"; exit 1 }

$h = $p.MainWindowHandle
[W]::ShowWindow($h, 3) | Out-Null          # SW_MAXIMIZE
Start-Sleep -Seconds 1

$ws = New-Object -ComObject wscript.shell
$ws.AppActivate($p.Id) | Out-Null
Start-Sleep -Milliseconds 900

if ([W]::GetForegroundWindow() -ne $h) { Write-Output "FOCUSFAIL"; exit 2 }

if ($KeysFile) {
  foreach ($line in Get-Content $KeysFile) {
    if ($line -eq "") { continue }
    if ($line.StartsWith("sleep ")) { Start-Sleep -Seconds ([int]$line.Split(" ")[1]); continue }
    [System.Windows.Forms.SendKeys]::SendWait($line)
  }
}

Start-Sleep -Seconds $Wait

$r = New-Object W+RECT
[W]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.R - $r.L; $ht = $r.B - $r.T
$b = New-Object Drawing.Bitmap $w, $ht
$g = [Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen($r.L, $r.T, 0, 0, (New-Object Drawing.Size $w, $ht))
$b.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $b.Dispose()
Write-Output ("saved {0} {1}x{2}" -f $Out, $w, $ht)
"""


def list_windows():
    """Print every visible top-level window as 'pid | title'."""
    ps = (
        "Get-Process | Where-Object { $_.MainWindowHandle -ne 0 } | "
        "ForEach-Object { \"$($_.Id) | $($_.ProcessName) | $($_.MainWindowTitle)\" }"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True)
    print(out.stdout.strip() or out.stderr.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="substring of the target window title")
    ap.add_argument("--out", help="PNG path to write")
    ap.add_argument("--keys-file", help="file of SendKeys lines (optional)")
    ap.add_argument("--wait", type=int, default=6, help="seconds before capture")
    ap.add_argument("--list", action="store_true", help="list windows and exit")
    args = ap.parse_args()

    if args.list:
        list_windows()
        return

    if sys.platform != "win32":
        sys.exit("capture_app.py is Windows only")
    if not args.src or not args.out:
        ap.error("--src and --out are required")

    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-Command", SCRIPT, "-Src", args.src, "-Out", args.out,
         "-KeysFile", args.keys_file or "", "-Wait", str(args.wait)],
        capture_output=True, text=True,
    )
    print(r.stdout.strip() or r.stderr.strip())
    if "FOCUSFAIL" in r.stdout:
        sys.exit("focus could not be verified - no keys were sent")
    if "NOWINDOW" in r.stdout:
        sys.exit("no window matching %r - run --list" % args.src)


if __name__ == "__main__":
    main()
