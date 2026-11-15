@echo off
REM LineageOS 23.2 GSI -> Moto G60 / G40 Fusion (hanoip) - fastboot installer
REM Phone must be in BOOTLOADER mode (Power + Vol Down), bootloader UNLOCKED.
cd /d "%~dp0"
where fastboot >nul 2>nul || (echo fastboot not found. Install Android platform-tools and add to PATH. & pause & exit /b 1)
if not exist system.img (echo system.img missing next to this script. & pause & exit /b 1)

fastboot devices
fastboot getvar product
echo.
echo Product above must be: hanoip  (Moto G60 / G40 Fusion)
echo This will ERASE ALL DATA on the phone (factory reset).
set /p OK=Type YES to continue: 
if not "%OK%"=="YES" (echo Aborted. & pause & exit /b 1)

echo == 1/4 Disable verified boot (bootloader) ==
fastboot --disable-verity --disable-verification flash vbmeta vbmeta_disabled.img || (echo vbmeta flash failed & pause & exit /b 1)
fastboot --disable-verity --disable-verification flash vbmeta_system vbmeta_disabled.img

echo == 2/4 Reboot to fastbootd ==
fastboot reboot fastboot
timeout /t 8 >nul

echo == 3/4 Make room in super and flash GSI ==
fastboot delete-logical-partition product
fastboot delete-logical-partition system_ext
fastboot erase system
fastboot flash system system.img || (echo system flash failed & pause & exit /b 1)

echo == 4/4 Wipe data and reboot ==
fastboot -w
fastboot reboot
echo Done. First boot can take 2-5 minutes.
pause
