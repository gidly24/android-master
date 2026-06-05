[app]
title = Task Control
package.name = taskcontrol
package.domain = org.example

source.dir = .
source.include_exts = py,png,ttf,db,env

version = 2.0

requirements = python3,kivy==2.3.1,certifi,pyjnius,android-notify

# Папки с ресурсами
source.include_patterns = assets/*, ui/*.py

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECEIVE_BOOT_COMPLETED, SCHEDULE_EXACT_ALARM, POST_NOTIFICATIONS, VIBRATE, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34

# Java BroadcastReceiver for AlarmManager reminders
android.add_src = android/

android.enable_androidx = True

android.gradle_dependencies = androidx.core:core:1.13.1

p4a.hook = p4a_hooks.py

[buildozer]
log_level = 2
warn_on_root = 1
