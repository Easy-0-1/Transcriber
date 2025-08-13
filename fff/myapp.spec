# -*- mode: python ; coding: utf-8 -*-
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''

a = Analysis(
    ['fff.py'],
    pathex=[],
    binaries=[],
    datas=[('ffmpeg-2025-07-23-git-829680f96a-full_build','ffmpeg-2025-07-23-git-829680f96a-full_build'),('recognise','recognise'),("C:\\Users\\Easy\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\whisper\\assets",'whisper\\assets')],
    hiddenimports=['os','sys','ffmpeg','ffmpegg','whisper','abstract_voice'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='fmpegg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='in.ico'
)
