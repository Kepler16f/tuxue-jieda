# 原程序窗口操作辅助: . winops.ps1 Capture <out> / . winops.ps1 Click <x> <y> <clientX> <clientY>
param([Parameter(Position=0)][string]$Cmd = "shot",
      [Parameter(Position=1)][string]$Arg1 = "",
      [Parameter(Position=2)][string]$Arg2 = "",
      [Parameter(Position=3)][int]$Cx = 0,
      [Parameter(Position=4)][int]$Cy = 0)

Add-Type @'
using System;
using System.Runtime.InteropServices;
public class U32 {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr h);
  [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr h, IntPtr dc);
  [DllImport("gdi32.dll")] public static extern bool BitBlt(IntPtr d, int x, int y, int w, int ht, IntPtr s, int sx, int sy, uint rop);
  [DllImport("user32.dll")] public static extern bool RedrawWindow(IntPtr h, IntPtr p, IntPtr g, uint f);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, IntPtr e);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  public struct RECT { public int L, T, R, B; }
}
'@
Add-Type -AssemblyName System.Drawing

$WIN = 1116780  # content window handle (refresh if program restarted)
$h = [IntPtr]$WIN

if ($Cmd -eq "shot") {
  [U32]::RedrawWindow($h, [IntPtr]::Zero, [IntPtr]::Zero, 0x0001 -bor 0x0100) | Out-Null
  Start-Sleep -Milliseconds 250
  $rc = New-Object U32+RECT
  [U32]::GetClientRect($h, [ref]$rc) | Out-Null
  $dc = [U32]::GetDC($h)
  $bmp = [System.Drawing.Bitmap]::new($rc.R, $rc.B)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $hdc = $g.GetHdc()
  [U32]::BitBlt($hdc, 0, 0, $rc.R, $rc.B, $dc, 0, 0, 0x00CC0020) | Out-Null
  $g.ReleaseHdc($hdc); $g.Dispose()
  [U32]::ReleaseDC($h, $dc) | Out-Null
  $out = if ($Arg1) { $Arg1 } else { "C:\Users\胡天泽\.zcode\workspace\default\_tuxue_web\tools\cap.png" }
  $bmp.Save($out); $bmp.Dispose()
  Write-Output ("shot saved: " + (Get-Item $out).Length + " bytes")
}
elseif ($Cmd -eq "click") {
  # 客户区坐标 (Arg1, Arg2)
  $x = [int]$Arg1; $y = [int]$Arg2
  $r = New-Object U32+RECT
  [U32]::GetWindowRect($h, [ref]$r) | Out-Null
  $rc = New-Object U32+RECT
  [U32]::GetClientRect($h, [ref]$rc) | Out-Null
  # 客户区左上角 = 窗口左上 + (边框, 标题栏)
  $ox = $r.L + [int](($r.R - $r.L - $rc.R) / 2)
  $oy = $r.T + ($r.B - $r.T - $rc.B - $ox + $r.L)
  $absx = $r.L + ($r.R - $r.L - $rc.R) / 2 + $x
  $absy = $r.B - $rc.B - (($r.B - $r.T - $rc.B) - ($r.B - $r.T - $rc.B - 0)) + 0
  # 简化: client 顶 = 窗顶 + (窗高-客户高-底边框); 用 GetWindowRect 差值均分不准, 直接经验值
  $titleH = ($r.B - $r.T) - $rc.B - 3
  $bordW = (($r.R - $r.L) - $rc.R - 6) / 2
  $absx = [int]($r.L + $bordW + $x)
  $absy = [int]($r.T + $titleH + $y)
  [U32]::BringWindowToTop($h) | Out-Null
  [U32]::SetForegroundWindow($h) | Out-Null
  Start-Sleep -Milliseconds 200
  [U32]::SetCursorPos($absx, $absy) | Out-Null
  Start-Sleep -Milliseconds 150
  [U32]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero)
  [U32]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)
  Write-Output ("clicked client($x,$y) -> screen($absx,$absy)")
}
