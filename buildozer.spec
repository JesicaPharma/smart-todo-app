[app]
title = 智能任务助手
package.name = smarttodo
package.domain = org.jessica
source.dir = .  
source.main = main.py
version = 0.1
requirements = python3,kivy
orientation = portrait
osx.python_version = 3.9
osx.kivy_version = 2.3.1

# 安卓权限
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# 安卓版本与架构
android.api = 30
android.minapi = 21
android.arch = arm64-v8a
android.accept_sdk_license = True

# 日志级别
log_level = 2

[buildozer]
warn_on_root = 1
