cd /d "%~dp0"


@echo off

echo ========================================
echo       SIMPLE LEDGER BUILD SYSTEM
echo ========================================

echo.
echo Installing dependencies...

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Cleaning previous builds...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building application...

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "SimpleLedger" ^
    --collect-all openpyxl ^
    main.py

echo.
echo ========================================
echo BUILD COMPLETE
echo ========================================

echo.
echo Your application is here:
echo dist\SimpleLedger\SimpleLedger.exe

pause