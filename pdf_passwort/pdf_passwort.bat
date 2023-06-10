@echo off
chcp 65001 >NUL
setlocal enabledelayedexpansion

set /P mode="Wählen Sie den Modus (1- Verschlüsseln, 2- Entschlüsseln): "
if "%mode%"=="1" ( set "operation=" ) else ( set "operation=--remove-password" )

rem Initialize an empty string to hold all the converted paths
set "allPaths="

rem Loop through all command line arguments (the dropped files)
for %%I in (%*) do (
    rem Remove quotes from the path
    set "winPath=%%~I"

    rem Convert the Windows-style path to a WSL-style path
    for /f "delims=" %%G in ('wsl wslpath "!winPath!"') do (
        set "wslPath=%%G"
    )

    rem Append the converted path to the string of all paths
    set "allPaths=!allPaths! "!wslPath!""
)
rem Pass all the converted paths to your Bash script
wsl bash pdf_passwort.sh %operation% !allPaths!


endlocal
