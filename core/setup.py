# -*- coding: utf-8 -*-
'''
Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
    http://license.coscl.org.cn/MulanPSL2
'''

from setuptools import setup, Extension
from Cython.Build import cythonize
# import platform
extra_compile_args = []
extra_link_args = []

# if platform.system() in ["Linux", "Darwin"]:  # Linux 或 macOS
#     # 速度优先优化：-O3 是最高级别的速度优化
#     # -march=native 让编译器针对当前CPU架构优化（可选，增强速度但可能降低兼容性）
#     extra_compile_args = ["-O3", "-march=native", "-Wall"]
    
#     # 剥离调试符号（不影响运行速度，仅减小体积）
#     extra_link_args = ["-s"]
# elif platform.system() == "Windows":  # Windows（使用 MSVC 编译器）
#     # 速度优先优化（MSVC 参数）
extra_compile_args = ["/O2", "/Ot", "/Wall"]  # /O2 速度优化，/Ot 优先速度
# 剥离调试符号（MSVC 链接参数）

# 移除调试信息
def k(q):
    extra_link_args = ["/RELEASE",f"/EXPORT:PyInit_{q}"]
    extensions = [
        Extension(
            q,
            sources=[f"{q}.pyx"],  # 替换为你的源文件
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args
        )
    ]
    setup(
        name=q,
        ext_modules=cythonize(extensions)
    )
# k('doc_to_docx')
# k('ffmpeeg')
# k('jpg_to_pdf')
# k('pdf')
# k('png_to_jpg')
# k('Ui_cutpi')
# k('Ui_cutvdo')
# k('Ui_fps')
# k('Ui_frontbebind')
# k('Ui_gif')
# k('Ui_key')
# k('Ui_markrotatetrainkle')
# k('Ui_mode')
# k('Ui_piform')
# k('Ui_tiaoz')
# k('Ui_wd')
# k('Ui_zim')
# k('Ui_viwtmk')
# k('UI004')
# k('cy')
# k('pxmm')
# k('spzm1')
# k('tpbl')
# k('aes256split')

# k('demo3')
# k('PPOCR_api')

# k('parser_multi_para')
# k('tbpu')

k('gap_tree')
k('line_preprocessing')
k('paragraph_parse')