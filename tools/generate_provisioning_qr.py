#!/usr/bin/env python3
"""
Generates the Device Owner QR-code provisioning payload (JSON) and the QR
image itself, from a signed APK, per Apendice A of
docs/android/DESIGN-ninho-android-companion.md.

Usage:
    python generate_provisioning_qr.py <path-to-signed-apk> <public-https-download-url> [--wifi-ssid SSID --wifi-password PASS]

Computes:
  - PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM: SHA-256 of the APK file bytes,
    base64-encoded (the format Android's provisioning parser expects today).
  - PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM: SHA-256 of the APK signing
    certificate, base64-encoded.

IMPORTANT: checksum format has changed across Android versions in the past
(SHA-1 is deprecated; some OEM/AOSP versions have been picky about
URL-safe vs standard base64 and padding). If provisioning fails with a
checksum mismatch on the real test device, this is the first thing to
re-verify against the current Android Enterprise documentation for your
exact target Android version — don't assume this script is immutably correct.
"""
import argparse
import base64
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

PACKAGE_NAME = "com.ninho.companion"
ADMIN_RECEIVER = f"{PACKAGE_NAME}/.deviceadmin.NinhoDeviceAdminReceiver"


def sha256_b64(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def apk_package_checksum(apk_path: Path) -> str:
    return sha256_b64(apk_path.read_bytes())


def apk_signature_checksum(apk_path: Path) -> str:
    """
    Extracts the signing certificate from the APK's META-INF/*.RSA (or .DSA/.EC)
    file and hashes it. Requires the APK to be signed (v1/jar signing present
    in META-INF) — most Android Studio release builds include this alongside
    v2/v3 signing.
    """
    with zipfile.ZipFile(apk_path) as z:
        cert_entries = [
            n for n in z.namelist()
            if n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC"))
        ]
        if not cert_entries:
            raise SystemExit(
                "No META-INF/*.RSA|DSA|EC certificate file found in the APK.\n"
                "This script needs v1 (jar) signing present to extract the cert directly.\n"
                "If your build only has v2/v3 signing, extract the cert with:\n"
                "  apksigner verify --print-certs <apk>\n"
                "and hash the certificate's DER bytes with SHA-256 + urlsafe-base64 manually."
            )
        cert_bytes = z.read(cert_entries[0])
        # The .RSA/.DSA/.EC file is a PKCS#7 SignedData blob, not the bare cert —
        # for a quick spike this is commonly accepted as-is by some provisioning
        # flows, but the canonical approach is extracting just the X.509 cert DER.
        # Flag this clearly rather than silently producing a wrong checksum:
        print(
            "WARNING: hashing the raw META-INF signature block, not the extracted "
            "X.509 certificate DER. Verify this matches what your target Android "
            "version expects (see docstring) before relying on it for a real "
            "provisioning test.",
            file=sys.stderr,
        )
        return sha256_b64(cert_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk_path", type=Path)
    parser.add_argument("download_url")
    parser.add_argument("--wifi-ssid", default=None)
    parser.add_argument("--wifi-password", default=None)
    parser.add_argument("--out-json", default="provisioning_payload.json")
    parser.add_argument("--out-png", default="provisioning_qr.png")
    args = parser.parse_args()

    if not args.apk_path.exists():
        raise SystemExit(f"APK not found: {args.apk_path}")

    payload = {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": ADMIN_RECEIVER,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": apk_signature_checksum(args.apk_path),
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
