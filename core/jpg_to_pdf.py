# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
from PIL import Image
import ctypes
from ctypes import wintypes
def pg(q):
    def jpg2pdf(jpgFile):
        img = Image.open(jpgFile)
        return images.append(img)
    def jpg2pdfByPath(files):
        for f in files:
            jpg2pdf(f)#单个文件
    images = []
    jpg2pdfByPath(q)#列表
    images[0].save(get_desktop_path()+'\\output.pdf', "PDF", save_all = True, quality=100, append_images = images[1:])
    #print('已保存至桌面，重命名以免被覆盖。')
#print('如转换失败，先用图片转换功能转为jpg格式。')
def get_desktop_path(): # pyright: ignore[reportSelfClsParameterName]
        CSIDL_DESKTOP = 0x0000
        SHGFP_TYPE_CURRENT = 0
        buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        #创建Unicode缓冲区
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buffer)
        #调用Windows的API来获取桌面路径
        desktop_path = buffer.value
        #将将缓冲区的值，赋给变量desktp_path
        return desktop_path