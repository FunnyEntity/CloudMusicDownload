@echo off
echo ========================================
echo    CloudMusic Download Builder
echo ========================================
echo.

echo [1/4] Cleaning old build files...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist *.spec del /q *.spec 2>nul
if exist "MusicDownload.exe" del /q "MusicDownload.exe" 2>nul
echo Clean completed!
echo.

echo [2/4] Building EXE...
if exist icon.ico (
    echo [INFO] Found icon.ico, using as app icon
    pyinstaller --onefile --windowed --icon=icon.ico --add-data="icon.ico;." --name="MusicDownload" --distpath="." musicdownload.py
) else (
    echo [INFO] No icon.ico found, using default icon
    pyinstaller --onefile --windowed --name="MusicDownload" --distpath="." musicdownload.py
)
echo.

if %ERRORLEVEL% EQU 0 (
    echo [3/4] Build Success!
    echo.

    echo [4/4] Cleaning build artifacts...
    if exist build rmdir /s /q build 2>nul
    if exist dist rmdir /s /q dist 2>nul
    if exist *.spec del /q *.spec 2>nul
    echo Clean completed!
    echo.

    echo EXE file: MusicDownload.exe
    echo.
) else (
    echo [3/4] Build Failed, check errors above.
)
echo.
echo Press any key to exit...
pause >nul
