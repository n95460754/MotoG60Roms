# ios-hanoip — iOS 16 на Moto G60 (порт на ios-sweet)

Порт на [ios-sweet](https://github.com/dipa-studio/ios-sweet) (MIT) за Moto G60 / G40 Fusion (`hanoip`).
Двата телефона са със **същия чип Snapdragon 732G (sdmmagpie)**, затова почти целият код важи и за G60.

> ⚠️ **Експериментално. Не е тествано на истински G60.** Инсталацията **изтрива всички данни в Android**.
> Ползвай резервен телефон и първо направи backup (стъпка 1). Нужен е **отключен bootloader**.

## Статус

| Етап | Статус |
|---|---|
| Хардуерни данни от device tree-то на Motorola | ✅ събрани (виж по-долу) |
| Екран 1080×2460, показан като iPhone X | ✅ patch `0082`, приложен и проверен |
| Всички 82 patch-а се прилагат на чист XNU 8796.141.3 | ✅ проверено локално и в CI |
| Shim компилиран за ARM64 | ✅ 0 предупреждения |
| Компилиране на XNU kernel | ⏳ GitHub Actions (`xnu-hanoip.yml`) |
| Първо пускане на телефона | ❌ още не е пробвано |
| Тъч (Ilitek по SPI) | ❌ нужен е нов драйвер, засега `sweettouch=0` |
| Wi‑Fi, GPS, мобилна мрежа, звук, GPU | ❌ не работят и на оригиналния sweet |

## Разлики между sweet и hanoip

Взети от Motorola kernel source (`sdmmagpie-hanoip-*`, `hanoi-panel.dtsi`, `sdmmagpie-hanoi-touchscreen.dtsi`):

| | Redmi Note 10 Pro (sweet) | Moto G60 (hanoip) | Действие |
|---|---|---|---|
| SoC | SM7150 / 732G | SM7150 / 732G (sdmmagpie) | същото |
| Framebuffer | `0x9c000000` | `0x9c000000` (`cont_splash_region`) | същото |
| Панел | 1080×2400 DSC video | 1080×2460 DSC video, Tianma ILI7807S | **patch 0082** |
| Volume up | PM6150L GPIO2 | PM6150L GPIO2 | същото |
| Power / volume down | PM6150 PON | PM6150 PON (стандартно) | да се потвърди на телефона |
| Тъч | Goodix GT9896, I²C, SE7 `0xa84000` | **Ilitek (TDDI), SPI, SE6 `0xa80000`**, reset GPIO 8, IRQ GPIO 9 | **нов драйвер** |
| Захранване на тъча | PM6150L LDO11 през RPMh | идва от панела (TDDI) | без LDO11 |
| Памет | upper bank `0x1_0000_0000 + 0xfcc00000` (6 GB) | да се прочете от телефона (4 GB и 6 GB се различават) | `hanoip-check-fdt.py` |

### Защо patch 0082

Кодът на sweet показва iOS като iPhone X (1125×2436) само когато панелът е **по-нисък** от 2436 реда.
Панелът на G60 е 2460, затова би паднал в „native“ режим, а за 1080×2460 iOS няма оформление.
Patch 0082:
- приема панел до 64 реда по-висок от iPhone X и показва 12 черни реда горе и долу (letterbox);
- изчиства тези редове веднъж, за да не остане логото на bootloader-а;
- смята тъча спрямо 2460 и пренася докосванията от черните ленти към най-близкия ред;
- сменя ранната конзола на 2460 реда.

## Стъпки

### 1. Backup (задължително)
```bash
fastboot boot twrp-hanoip.img          # временно, нищо не се флашва
tools/hanoip-backup.sh backup/
```
Копира `persist`, `modemst1/2`, `fsg`, `fsc`, `utags`, `hw`, `cid`, boot/dtbo/vbmeta и device tree-то.
Тези дялове са **уникални за твоя телефон** (IMEI, калибрации). Пази `backup/` извън git и облака.

### 2. Провери device tree-то
```bash
python3 tools/hanoip-check-fdt.py backup/dtb/live-fdt.dtb
```
Трябва да е 0 FAIL. Скриптът казва и какво да се сложи в `tools/mkadt.py` за паметта (`HIGH_PHYS_BASE`, `HIGH_MEM_SIZE`).

### 3. Провери boot образа
ios-sweet очаква boot image **v2** с DTB в него. Провери копието си:
```bash
python3 tools/unpack_bootv2.py backup/partitions/boot_a.img dtb/boot_unpacked
```
Ако даде грешка за версията, **спри**. Тогава shim-ът трябва да се пакетира различно (сайтът hackiosx.dev описва точно този капан).

### 4. Kernel, iOS образ и boot
Както в `README.md` на ios-sweet, стъпки 1–4, но:
- kernel-ът идва от artifact `xnu-kernel-hanoip` в GitHub Actions;
- boot-args са в `tools/hanoip-cmdline.txt` (`cpus=1`, `sweettouch=0` и без `sweetfb_noconsole`, за да се вижда текстът на kernel-а при първото пускане).

```bash
python3 tools/mkpayload.py xnu/out/kernel.development.sweet shim/out/sweet.adt shim/out/payload.bin \
    --cmdline "$(cat tools/hanoip-cmdline.txt)"
```

## Проверка за грешки

```bash
python3 tools/validate-repo.py                       # номерация на patch-овете, Python и shell синтаксис
bash tools/check-patches.sh "$PWD" <xnu-8796.141.3> <darwin-xnu-build> /tmp/work   # всеки patch строго
```
Внимание: `build.sh` на darwin-xnu-build само **предупреждава** при patch, който не се прилага, и продължава.
`check-patches.sh` и workflow-ът `xnu-hanoip.yml` спират при такъв patch.

## Следващата голяма задача: тъч

G60 има Ilitek TDDI на SPI шина (QUP SE6). Нужни са:
1. GENI SPI драйвер (sweet има само GENI I²C);
2. протоколът на Ilitek v3 (Linux драйверът `ilitek_v3_mmi` в kernel-а на Motorola е отправната точка);
3. reset през TLMM GPIO 8 и прекъсване на GPIO 9.

## Credits
ios-sweet от dipa-studio (MIT, виж `LICENSE`). Хардуерните данни са от публикувания kernel на Motorola
(`motorola-sm6150-devs/kernel_motorola_sm6150`). iOS е собственост на Apple и не се разпространява тук.
