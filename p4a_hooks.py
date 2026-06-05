import os
import xml.etree.ElementTree as ET


ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = f"{{{ANDROID_NS}}}"
RECEIVER_NAME = "org.kivy.android.PythonBroadcastReceiver"

ET.register_namespace("android", ANDROID_NS)


def _patch_manifest(path):
    if not os.path.exists(path):
        return

    tree = ET.parse(path)
    root = tree.getroot()
    application = root.find("application")
    if application is None:
        return

    for receiver in application.findall("receiver"):
        if receiver.get(f"{ANDROID}name") == RECEIVER_NAME:
            receiver.set(f"{ANDROID}enabled", "true")
            receiver.set(f"{ANDROID}exported", "false")
            break
    else:
        application.append(ET.Element("receiver", {
            f"{ANDROID}name": RECEIVER_NAME,
            f"{ANDROID}enabled": "true",
            f"{ANDROID}exported": "false",
        }))

    ET.indent(tree, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def after_apk_build(ctx):
    _patch_manifest(os.path.join("src", "main", "AndroidManifest.xml"))
    _patch_manifest("AndroidManifest.xml")
