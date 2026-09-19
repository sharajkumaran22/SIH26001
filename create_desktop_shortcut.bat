@echo off
TITLE Create LAND-SAFE AI Desktop Shortcut
echo Creating desktop shortcut for LAND-SAFE AI...

set SCRIPT="%TEMP%\CreateShortcut.vbs"
set TARGET=%~dp0run_app.bat
set ICON=%~dp0frontend\icon-512.png
set WORKING=%~dp0

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\LAND-SAFE AI.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%TARGET%" >> %SCRIPT%
echo oLink.WorkingDirectory = "%WORKING%" >> %SCRIPT%
echo oLink.Description = "LAND-SAFE AI - Early Warning & Landslide Risk Monitoring System" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo =====================================================================
echo  SUCCESS! A shortcut named "LAND-SAFE AI" has been created on your
echo  Windows Desktop! You can now double-click it anytime to open the app.
echo =====================================================================
pause
