# LineageOS 23.2 GSI — Moto G60 / G40 Fusion (hanoip)

Fastboot zip пакет, направен от [MisterZtr/LineageOS_gsi v2026.05.24-lineage23.2](https://github.com/MisterZtr/LineageOS_gsi/releases/tag/v2026.05.24-lineage23.2)
(Android 16 QPR2, неофициален билд). Готовите zip-ове са в **Releases** на това repo.

| Файл | Какво е |
|---|---|
| `LineageOS-23.2-20260524-VANILLA-EXT4-hanoip.zip` | без Google приложения |
| `LineageOS-23.2-20260524-GAPPS-EXT4-hanoip.zip` | с Google Play |

Защо **EXT4**, а не EROFS: EROFS изисква kernel 5.4+, а G60 (Snapdragon 732G) е на 4.14 → EROFS няма да зареди.

## Какво има в zip-а
- `system.img` – самият GSI
- `vbmeta_disabled.img` – празен vbmeta с изключена проверка (flags=2), генериран от `tools/make_blank_vbmeta.py`
- `flash-all.bat` (Windows) / `flash-all.sh` (Linux/macOS)
- `SHA256SUMS`

## Инсталация
1. Отключен bootloader (Motorola unlock), последен stock firmware (Android 11/12).
2. Инсталирай [Android platform-tools](https://developer.android.com/tools/releases/platform-tools).
3. Разархивирай zip-а, телефонът в **bootloader** (Power + Vol−), свържи USB.
4. Пусни `flash-all.bat` или `./flash-all.sh` и напиши `YES`.

Скриптът прави това (същото като XDA ръководството за G40/G60):
```
fastboot --disable-verity --disable-verification flash vbmeta vbmeta_disabled.img
fastboot --disable-verity --disable-verification flash vbmeta_system vbmeta_disabled.img
fastboot reboot fastboot
fastboot delete-logical-partition product
fastboot delete-logical-partition system_ext
fastboot erase system
fastboot flash system system.img
fastboot -w
fastboot reboot
```

⚠️ Изтрива всички данни. Това е **fastboot** пакет, не TWRP zip — GSI на dynamic partitions се флашва най-сигурно през fastbootd.
Връщане назад: флашни stock firmware (напр. с Motorola Rescue and Smart Assistant).

## Билд
`.github/workflows/build-g60-gsi-zip.yml` тегли 7z от SourceForge, вади `.img`, пакетира и качва в Releases.

## PixelOS 16 (специално за hanoip, не GSI)
Отделен релийз `g60-pixelos16.2-20261102`: огледало на [PixelOS 16.2 от luizpaulo2005](https://github.com/luizpaulo2005/pixelos-hanoip)
(`.zip` за `adb sideload` + `boot`/`vendor_boot`/`dtbo`/`vbmeta`). Изисква stock Android 12 firmware.
Обаждания/SMS/мобилни данни още не са тествани от автора. Workflow: `.github/workflows/mirror-pixelos-g60.yml`.
