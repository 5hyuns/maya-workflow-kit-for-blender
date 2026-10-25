$root = "C:\Repos\blender-maya-kit"
New-Item -ItemType Directory -Force "$root\tmp\maya_app_ge198" | Out-Null
$env:MAYA_APP_DIR = "$root\tmp\maya_app_ge198"
$env:PYTHONPATH = "$root\research\scripts\maya_ge198"
$env:MK_SHOTS_SCRIPT = "$root\research\scripts\maya_ge198\ge198.py"
$env:MK_SHOTS_OUT = "$root\tmp\maya_ge198_out"
$env:MAYA_DISABLE_CIP = "1"; $env:MAYA_DISABLE_CER = "1"; $env:MAYA_DISABLE_ADP = "1"; $env:MAYA_NO_HOME = "1"
$env:MAYA_NO_WARNING_FOR_MISSING_DEFAULT_RENDERER = "1"
$p = Start-Process -FilePath "C:\Program Files\Autodesk\Maya2022\bin\maya.exe" -ArgumentList "-log","$root\tmp\maya_ge198.log" -PassThru
$p.Id
