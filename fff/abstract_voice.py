# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''

import os
import sys
import whisper

def get_path(relative_path):
        try:
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue] # pyinstaller打包后的路径
        except AttributeError:
            base_path = os.path.abspath(".") # 当前工作目录的路径
        return os.path.normpath(os.path.join(base_path, relative_path))

class g():
    
    def __init__(self, ffmpeg_path=get_path(r'ffmpeg-2025-07-23-git-829680f96a-full_build\bin')):
        """
        初始化FFmpeg工具类

        """
        self.ffmpeg_path = ffmpeg_path
        if ffmpeg_path:
            os.environ["PATH"] += os.pathsep + ffmpeg_path

    def g(self,inputfile:str,scale:str):
        # 加载模型，可选:small.pt, medium.pt
        try:
            model = whisper.load_model(os.path.join(get_path('recognise'),scale),'cuda')
        except Exception as e:
            print(e,'\n这是说GPU不支持特定cuda，将使用CPU处理。\nnvidia显卡可以在网上自行下载cuda以提高处理速度.')
            model = whisper.load_model(os.path.join(get_path('recognise'),scale))
        # 对音频文件进行转录
        result = model.transcribe(inputfile)
        # 打印转录文本
        for i in result['segments']:
            print({'start_time':i['start'],'end_time':i['end'],'text':i['text']},',') # pyright: ignore[reportArgumentType]

# a=g()
# a.g(scale='medium.pt',inputfile=r"D:\Easy\Videos\屏幕录制\屏幕录制 2025-07-29 195015.mp4")