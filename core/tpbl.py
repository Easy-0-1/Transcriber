# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
from PIL import Image


def image_clip(filename, width_scale, height_scale,w:str):
    """图像裁剪

    :param filename: 原图路径
    :param savename: 保存图片路径
    :param width_scale: 宽的比例
    :param height_scale: 高的比例
    """
    image = Image.open(filename)
    (width, height), (_width, _height) = image.size, image.size
    _height = width / width_scale * height_scale
    if _height > height:
        _height = height
        _width = width_scale * height / height_scale
    savename = filename+'result.png'
    if w=='rd':
        image.crop((0, 0, _width, _height)).save(savename)  # 左上角     #裁剪右下角
    elif w=='ru':
        image.crop((0, height - _height, _width, height)).save(savename)  # 左下角
    elif w=='ld':
        image.crop((width - _width, 0, width, _height)).save(savename)  # 右上角
    elif w=='lu':
        image.crop((width - _width, height - _height, width, height)).save(savename)  # 右下角



