import os
import sys
import subprocess
from pathlib import Path
import pythoncom
import ctypes
from ctypes import wintypes

import winshell

def self_restart():
    if getattr(sys, 'frozen', False):
        try:
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit()
        except Exception as e:
            print("重啟失敗:", e)
            print("需要手動重啟")
    else:
        python = sys.executable
        script = os.path.abspath(__file__)
        os.execvp(python, [python, script])

def update_package(package_name):
    print(f"檢查chrome套件更新...")
    try:
        # 使用subprocess调用pip命令来更新指定的套件
        subprocess.check_call(['python.exe', '-m', 'pip', 'install', '--upgrade', "pip"])
        subprocess.check_call(['python.exe', '-m', 'pip', 'install', '--upgrade', package_name])
        print(f"檢查完成")
    except subprocess.CalledProcessError:
        print(f"{package_name} 更新失敗")