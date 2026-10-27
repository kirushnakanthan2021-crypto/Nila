# Build, release, and update Nila Android APK

The APK is built in GitHub Actions, so a PC is not required.

## Download the latest APK

1. Open the repository's **Releases** page: https://github.com/kirushnakanthan2021-crypto/Nila/releases
2. Open the latest release.
3. Under **Assets**, download `Nila-v1.0.X.apk` (the exact version number changes).
4. Open the downloaded APK from Android Downloads and confirm installation.

You can also open **Actions → Build and release Nila Android APK** to inspect the build. The workflow creates a versioned APK artifact and publishes it as a GitHub Release.

## In-app update prompt

When Nila starts, it checks the latest GitHub Release. If a newer version is available, Nila shows an **Update available** banner. Tap **Download update**, download the APK, then open it from Downloads and confirm installation. Android may require installation permission/confirmation.

## Important first-upgrade note

The APK previously installed from early workflow runs used a temporary signing key. The new workflow preserves its signing key in the GitHub Actions cache for future builds, but Android cannot update an app signed with a different key. For the first move to the release-based updater, export a Nila backup first if you have important notes, uninstall the old Nila app, then install the first APK published by this new workflow. After that, later workflow builds should use the preserved signing key and install as updates, as long as the GitHub Actions cache remains available.

This is a debug/testing APK, not a Play Store release. It wraps the current Nila web app; it does not by itself add a generative AI model or autonomous learning engine. Keep private API tokens out of source code.
