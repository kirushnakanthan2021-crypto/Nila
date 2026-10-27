# Build and download the Nila Android APK

The APK is built in GitHub Actions; you do not need a PC to run the build.

1. Open the repository's **Actions** tab.
2. Select **Build Nila Android APK**.
3. Tap **Run workflow** and confirm.
4. Wait for the workflow to finish successfully.
5. Open that completed run, scroll to **Artifacts**, and download **Nila-Android-APK**.
6. Extract the downloaded ZIP on your Android phone and install `app-debug.apk`. Android may ask you to allow installs from that browser/file manager.

This is a debug APK for testing, not a Play Store release. It wraps the current Nila web app; it does not by itself add a generative AI model or autonomous learning engine. Keep private API tokens out of source code.
