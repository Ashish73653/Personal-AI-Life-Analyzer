# PALA Android App (Phase 2)

This is the Android client setup for PALA.

## Prerequisites

- Android Studio (recommended for SDK setup)
- Android SDK 35
- JDK 17

## Open and run

1. Open the `android` folder in Android Studio or VS Code.
2. If using VS Code, ensure Android SDK + Gradle tooling are installed.
3. Sync Gradle.
4. Run on an emulator or device.

## SDK setup (required for first build)

If `assembleDebug` fails with `SDK location not found`, create `android/local.properties` with:

```properties
sdk.dir=C:\\Users\\<your-user>\\AppData\\Local\\Android\\Sdk
```

Or set `ANDROID_HOME` to your SDK location.

## Backend URL

Debug build uses:

- `http://10.0.2.2:8000/` for Android emulator

If you run on a physical phone, update `BASE_URL` in `app/build.gradle.kts` to your machine's LAN IP.

## Run on physical phone (no emulator)

1. Start backend so phone can reach it:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. Find your PC LAN IP (example `192.168.1.10`) and set debug BASE_URL in `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "BASE_URL", "\"http://192.168.1.10:8000/\"")
```

3. Connect phone by USB and enable USB debugging.
4. Verify device connection:

```bash
adb devices
```

5. Install app from `android/` folder:

```bash
./gradlew :app:installDebug
```

6. Open app on phone and test login/register.

Note: cleartext HTTP is enabled in `AndroidManifest.xml` + `network_security_config.xml` for local development.

## Current setup included

- Compose UI shell
- Auth screens and ViewModel
- Retrofit API client
- Hilt dependency injection
- Secure token storage
- Room database starter
- WorkManager sync worker placeholder
- Step tracking service placeholder
