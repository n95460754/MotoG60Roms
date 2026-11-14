# TrackPack — TWRP zip за Moto G60 (hanoip)

Flashable zip, който инсталира приложения за проследяване с GPS, Wi‑Fi и мобилна мрежа:

| Приложение | Пакет | Мин. Android | Какво прави |
|---|---|---|---|
| [GpsTracker](https://github.com/nickfox/GpsTracker) | `com.websmithing.gpstracker` | 8 (SDK 26) | Праща GPS позицията към твой сървър |
| [Fieldwatch](https://github.com/OffGridPete/Fieldwatch) | `app.fieldwatch` | 10 (SDK 29) | Сканира Wi‑Fi/Bluetooth + GPS |
| [mobile-phone-proxy](https://github.com/stepanic/mobile-phone-proxy) | `com.stepanic.mobilephoneproxy` | **12 (SDK 31)** | Ползва мобилните данни на телефона като proxy |

`traccar/traccar` е **сървър** (Java), не Android приложение, затова не е в zip-а.
Пусни го на компютър или VPS, а GpsTracker (или Traccar Client) праща към него.

## Как се получава zip-ът

* **GitHub Actions**: Actions → *Build TrackPack* → *Run workflow* → изтегли artifact `TrackPack-MotoG60`.
  Компилира GpsTracker и mobile-phone-proxy от изходния код и добавя официалния APK на Fieldwatch.
* **Локално**: сложи APK файловете в една папка и пусни
  `./build.sh <папка-с-apk> out/TrackPack-MotoG60.zip` (трябват `zip` и `aapt` от Android build-tools).

## Режими на инсталация

Режимът се избира от **името на zip файла**:

* `TrackPack-MotoG60.zip` → **data режим (препоръчителен)**. APK-тата отиват в `/data/app`,
  а Android ги регистрира при първото пускане. `/system` не се пипа, затова няма риск от bootloop.
  Разрешенията (локация и т.н.) ги даваш ти, когато приложението ги поиска.
* `TrackPack-MotoG60-system.zip` (има „system“ в името) → приложенията стават **системни**
  (`/system/app`), а разрешенията за GPS, Wi‑Fi и известия са дадени предварително.
  ⚠️ Работи само ако dm-verity е изключен (Magisk или `vbmeta --disable-verity`),
  иначе телефонът няма да стартира. Ако `/system` е само за четене, скриптът сам минава на data режим.

## Флашване

1. Boot в TWRP → **Install** → избери zip-а → swipe.
2. **Wipe Dalvik/ART Cache** → **Reboot System**.
3. Първото пускане може да отнеме 1–3 минути.
4. Резервни копия на APK-тата има в *Вътрешна памет/TrackPack/*. Ако някое приложение не се появи, инсталирай го оттам на ръка.

## За GPU / модем / Wi‑Fi драйвери

Zip-ът **не** съдържа драйвери. Moto G60 вече ги има в стоковия vendor/firmware (Adreno 618, Qualcomm модем и Wi‑Fi).
Приложенията просто ползват GPS, Wi‑Fi и мобилната мрежа, които вече работят.
