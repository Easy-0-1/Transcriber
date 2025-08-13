# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import sys
import os
import multiprocessing as mp
from PyQt6.QtWidgets import QApplication,QSplashScreen
from PyQt6.QtGui import QPixmap,QFont,QColor
from PyQt6.QtCore import Qt
def get_path(relative_path):
        try:
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue] # pyinstaller打包后的路径
        except AttributeError:
            base_path = os.path.abspath(".") # 当前工作目录的路径
        return os.path.normpath(os.path.join(base_path, relative_path))

if __name__ == "__main__":
    # 启用多进程支持（Windows必需）
    mp.freeze_support()
    app = QApplication(sys.argv)
    splash = QSplashScreen(QPixmap(get_path("pictures\\微信图片_20250726172227.png")))
    splash.showMessage('Easy is the best!',Qt.AlignmentFlag.AlignCenter,QColor('yellow'))
    #一定要AlignmentFlag，多参用‘|’。QColor使用见Python文件夹截屏。
    splash.setFont(QFont('Times New Roman', 25))
    splash.show()
    import UI004
    window = UI004.MainWindow()
    splash.close()
    sys.exit(app.exec())