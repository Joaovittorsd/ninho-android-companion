#!/usr/bin/env python3
"""
Generates the Device Owner QR-code provisioning payload (JSON) and the QR
image itself, from a signed APK + its keystore, per Apendice A of
docs/android/DESIGN-ninho-android-companion.md.

Usage:
    python generate_provisioning_qr.py <path-to-signed-apk> <public-https-download-url> \
        --keystore <path-to-.jks> --alias <key-alias> \
        [--storepass PASSWORD] [--wifi-ssid SSID --wifi-password PASS]

If --storepass is omitted, you'll be prompted for it (not echoed to the
terminal via getpass, though note keytool itself may echo it if console
redirection prevents masked input — still never passed as a bare CLI arg,
so it won't land in shell history or process listings).

Computes:
  - PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM: SHA-256 of the APK file bytes,
    base64-encoded.
  - PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM: SHA-256 of the signing
    certificate, read directly from the keystore via `keytool`, base64-encoded.
    This works regardless of whether the APK uses v1/v2/v3 signing (modern
    Android Studio builds commonly skip v1/jar signing, which is why parsing
    META-INF directly from the APK doesn't work — reading the cert from the
    keystore that signed it sidesteps that entirely).

IMPORTANT: checksum format has changed across Android versions in the past
(SHA-1 is deprecated; some OEM/AOSP versions have been picky about
URL-safe vs standard base64 and padding). If provisioning fails with a
checksum mismatch on the real test device, this is the first thing to
re-verify against the current Android Enterprise documentation for your
exact target Android version — don't assume this script is immutably correct.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_NAME = "com.ninho.companion"
ADMIN_RECEIVER = f"{PACKAGE_NAME}/.deviceadmin.NinhoDeviceAdminReceiver"


def sha256_b64(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def apk_package_checksum(apk_path: Path) -> str:
    return sha256_b64(apk_path.read_bytes())


def find_keytool() -> str:
    found = shutil.which("keytool")
    if found:
        return found

    candidates = [
        Path(r"C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe"),
        Path(r"C:\Program Files\Android\Android Studio1.1\jbr\bin\keytool.exe"),
    ]
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidates.append(Path(java_home) / "bin" / "keytool.exe")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise SystemExit(
        "keytool not found on PATH or in common Android Studio locations.\n"
        "It ships with the JBR (JetBrains Runtime) bundled inside Android Studio.\n"
        "Either add this to your PATH and retry:\n"
        r'  C:\Program Files\Android\Android Studio\jbr\bin' + "\n"
        "...or pass its full path via the KEYTOOL_PATH environment variable."
    )


def signature_checksum_from_keystore(keystore_path: Path, alias: str, storepass: str | None) -> str:
    keytool = os.environ.get("KEYTOOL_PATH") or find_keytool()

    if storepass is None:
        storepass = getpass.getpass(f"Keystore password for {keystore_path.name}: ")

    env = os.environ.copy()
    env["NINHO_KS_PASS"] = storepass

    result = subprocess.run(
        [
            keytool, "-list", "-v",
            "-keystore", str(keystore_path),
            "-alias", alias,
            "-storepass:env", "NINHO_KS_PASS",
        ],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise SystemExit(
            f"keytool failed (exit code {result.returncode}).\n"
            f"keytool used: {keytool}\n"
            f"keystore: {keystore_path}\n"
            f"alias: {alias}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}\n"
        )

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("SHA256:"):
            hex_fingerprint = line.split("SHA256:", 1)[1].strip().replace(":", "")
            digest = bytes.fromhex(hex_fingerprint)
            return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    raise SystemExit(
        "Could not find a 'SHA256:' fingerprint line in keytool output. "
        "Full output below for debugging:\n" + result.stdout
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("apk_path", type=Path)
    parser.add_argument("download_url")
    parser.add_argument("--keystore", required=True, type=Path)
    parser.add_argument("--alias", required=True)
    parser.add_argument("--storepass", default=None, help="Omit to be prompted instead (recommended).")
    parser.add_argument("--wifi-ssid", default=None)
    parser.add_argument("--wifi-password", default=None)
    parser.add_argument("--out-json", default="provisioning_payload.json")
    parser.add_argument("--out-png", default="provisioning_qr.png")
    args = parser.parse_args()

    if not args.apk_path.exists():
        raise SystemExit(f"APK not found: {args.apk_path}")
    if not args.keystore.exists():
        raise SystemExit(f"Keystore not found: {args.keystore}")

    payload = {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": ADMIN_RECEIVER,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": signature_checksum_from_keystore(
            args.keystore, args.alias, args.storepass
        ),
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": args.download_url,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": apk_package_checksum(args.apk_path),
        "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": False,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": True,
    }

    if args.wifi_ssid:
        payload["android.app.extra.PROVISIONING_WIFI_SSID"] = args.wifi_ssid
        if args.wifi_password:
            payload["android.app.extra.PROVISIONING_WIFI_PASSWORD"] = args.wifi_password

    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_json.resolve()}")

    try:
        import qrcode
    except ImportError:
        print("qrcode package not installed — skipping QR image. JSON is still usable.")
        return

    img = qrcode.make(json.dumps(payload))
    out_png = Path(args.out_png)
    img.save(out_png)
    print(f"Wrote {out_png.resolve()}")
    print("\nScan this QR during the factory-reset setup screen (tap the welcome")
    print("screen 6 times to enter QR provisioning mode on stock Android setup wizard).")


if __name__ == "__main__":
    main()
