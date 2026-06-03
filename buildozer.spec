[app]
title = Task Control
package.name = taskcontrol
package.domain = org.example

source.dir = .
source.include_exts = py,png,ttf,db,env

version = 2.0

requirements = python3,kivy==2.3.1,certifi,pyjnius

# Папки с ресурсами
source.include_patterns = assets/*, android/*.java, ui/*.py

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECEIVE_BOOT_COMPLETED, SCHEDULE_EXACT_ALARM, POST_NOTIFICATIONS, VIBRATE
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34

# Java-файл для уведомлений
android.add_src = android/

# Регистрация BroadcastReceiver в манифесте
android.extra_manifest_xml = \
    <receiver android:name="org.kivy.android.PythonBroadcastReceiver" android:exported="false"> \
        <intent-filter> \
            <action android:name="com.taskcontrol.reminder"/> \
        </intent-filter> \
    </receiver>

[buildozer]
log_level = 2
warn_on_root = 1
