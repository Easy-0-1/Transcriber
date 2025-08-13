# cython: language_level=3
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
import ffmpeg

def get_path(relative_path):
        try:
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue] # pyinstaller打包后的路径
        except AttributeError:
            base_path = os.path.abspath(".") # 当前工作目录的路径
        return os.path.normpath(os.path.join(base_path, relative_path))

class FFmpegUtils:
    def create_input_stream(self,input_file):
        """创建输入流，支持指定起始时间和时长"""
        stream = ffmpeg.input(input_file)
        video_stream = stream.video
        audio_stream = stream.audio
        return video_stream ,audio_stream 
    def apply_high_quality_fps_filter(self,video_stream,w, target_fps=60):
        """应用高质量帧率转换滤镜""" 
        if w=='e':
            return video_stream.filter("deshake").filter(
                "minterpolate",
                fps=target_fps,         # 直接设置目标帧率
                # mi_mode="mci",          # 运动补偿插值
                #me_mode="bidir",        # 双向运动估计（前后帧参考）
                # me='umh',
                # mc_mode="aobmc",        # 高级重叠块运动补偿  
                # mb_size=8,              # 更小的宏块（8x8）捕获更精细的运动
                # search_param=500,       # 更大的搜索范围（提高精度但降低速度）
                # vsbmc=1,                # 可变大小块运动补偿
            )
        elif w=='h':
            return video_stream.filter("deshake").filter(
                "minterpolate",
                fps=target_fps,         # 直接设置目标帧率
                mi_mode="mci",          # 运动补偿插值
                me_mode="bidir",        # 双向运动估计（前后帧参考）
                me='umh',
                mc_mode="aobmc",        # 高级重叠块运动补偿  
                mb_size=16,              # 更小的宏块（8x8）捕获更精细的运动
                search_param=500,       # 更大的搜索范围（提高精度但降低速度）
                vsbmc=1,                # 可变大小块运动补偿
            )
    def save_output(self,video_stream, audio_stream,output_file, m,w):
        """保存处理后的流到输出文件""" 
        if audio_stream is not None:  #无效，还是报错（【为了与RELEASE一致，没有删了，但是实际上无声视频输入还是报错】
            '''
            Stream map '' matches no streams.
            To ignore this, add a trailing '?' to the map.
            Failed to set value '0:a' for option 'map': Invalid argument
            '''
            if m=='gpu':
                try:
                    stream1 = ffmpeg.output(
                        video_stream,
                        audio_stream,
                        output_file,
                        vcodec="h264_amf",       # 或 hevc_amf
                        preset="quality",        # 质量优先
                        level="5.1",             # 指定编码级别
                        bf=2,                    # B帧数量
                        g=120,                 # I帧间隔
                    ).global_args("-profile:v", "high")  # 明确指定视频profile         
                    return stream1.run(overwrite_output=True)
                except:
                    try:
                        stream2 = ffmpeg.output(
                            video_stream,
                            audio_stream,
                            output_file,
                            vcodec="h264_qsv",       # 或 hevc_qsv
                            preset="veryslow",        # 质量优先
                            # global_quality=18,       # QSV 质量参数（18-28）
                            level="5.1",
                            # b_strategy=1             # B帧策略
                        ).global_args("-profile:v", "high") .global_args("-look_ahead", "1")  # 启用预分析
                        return stream2.run(overwrite_output=True)
                    except Exception as e:
                        print(e,'用CPU试试')
            elif m=='cpu':
                stream3 = ffmpeg.output(
                    video_stream,
                    audio_stream,
                    output_file,
                    vcodec="libx264",        # 或 libx265 用于 H.265
                    preset="slow" if w=='h' else 'veryslow',       # 慢但质量高
                    crf=18,
                    # tune="animation",#用于动画
                    level="5.1",
                    bf=3,                    # B帧数量
                    qcomp=0.5,            # 量化复杂度
                    subq=10,           # 子像素运动估计迭代次数
                    deblock="-1:-1", 
                ).global_args("-threads", "0").global_args("-profile:v", "high") 
                return stream3.run()
        else:
            if m=='gpu':
                try:
                    stream1 = ffmpeg.output(
                        video_stream,
                        output_file,
                        vcodec="h264_amf",       # 或 hevc_amf
                        preset="quality",        # 质量优先
                        level="5.1",             # 指定编码级别
                        bf=2,                    # B帧数量
                        g=120,                 # I帧间隔
                    ).global_args("-profile:v", "high")  # 明确指定视频profile         
                    return stream1.run(overwrite_output=True)
                except:
                    try:
                        stream2 = ffmpeg.output(
                            video_stream,
                            output_file,
                            vcodec="h264_qsv",       # 或 hevc_qsv
                            preset="veryslow",        # 质量优先
                            # global_quality=18,       # QSV 质量参数（18-28）
                            level="5.1",
                            # b_strategy=1             # B帧策略
                        ).global_args("-profile:v", "high") .global_args("-look_ahead", "1")  # 启用预分析
                        return stream2.run(overwrite_output=True)
                    except Exception as e:
                        print(e,'用CPU试试')
            elif m=='cpu':
                stream3 = ffmpeg.output(
                    video_stream,
                    output_file,
                    vcodec="libx264",        # 或 libx265 用于 H.265
                    preset="slow" if w=='h' else 'veryslow',       # 慢但质量高
                    crf=18,
                    # tune="animation",#用于动画
                    level="5.1",
                    bf=3,                    # B帧数量
                    qcomp=0.5,            # 量化复杂度
                    subq=10,           # 子像素运动估计迭代次数
                    deblock="-1:-1", 
                ).global_args("-threads", "0").global_args("-profile:v", "high") 
                return stream3.run()
            

    # 构建处理流程
    def fps(self,input_file:str,target_fps,output_file="outputt.mp4",m='gpu',w='e'):
        input_stream,audio_stream = self.create_input_stream(input_file)
        processed_stream = self.apply_high_quality_fps_filter(input_stream,w, target_fps)
        self.save_output(processed_stream,audio_stream, os.path.splitext(input_file)[0]+output_file,m,w)
    
    #河流
    def together(self,VP:str,AP:str):
        video = ffmpeg.input(VP)
        audio = ffmpeg.input(AP)
        ffmpeg.output(
            video.video,  # 仅使用视频流
            audio.audio,  # 仅使用音频流
            'output.mp4',
            vcodec='copy',  # 复制视频，不重新编码
            acodec='aac',   # 音频转码为 AAC
            ab="320k",
            strict='experimental'
        ).run()

    def __init__(self, ffmpeg_path=get_path(r'ffmpeg-2025-07-23-git-829680f96a-full_build\bin')):
        """
        初始化FFmpeg工具类
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径，如果为None则使用系统路径
        """
        self.ffmpeg_path = ffmpeg_path
        if ffmpeg_path:
            os.environ["PATH"] += os.pathsep + ffmpeg_path
    
    def convert_to_h265(self, input_path: str, output_path: str='ooput.mp4') -> None:
        """
        将视频转换为H.265/HEVC编码，最高质量设置
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出视频文件路径
        """
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    os.path.splitext(input_path)[0]+output_path,
                    vcodec="libx265",
                    preset="veryslow",
                    crf=18,
                    acodec="aac",
                    ab="320k",
                    pix_fmt="yuv420p",
                    movflags="+faststart"
                )
                .run()
            )
            print(f"成功转换视频: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"转换视频失败: {e}")
            raise
    
    def extract_audio(self, input_path: str, output_path: str='opput.mp3') -> None:
        """
        从视频中提取音频
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出音频文件路径
        """
        try:
            (
                ffmpeg
                .input(input_path) # type: ignore
                .output(
                    os.path.splitext(input_path)[0]+output_path,
                    vn=None,  # 禁用视频流
                    acodec="libmp3lame",  # 使用 MP3 编码器
                    **{"q:a": 1}
                    #若需要无损格式输出，改这里。
                )
                .run()
            )
            print(f"成功提取音频: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"提取音频失败: {e}")
            raise
    
    def resize_video(self, input_path: str, width: int, height: int,output_path: str='opuut.mp4') -> None:
        """
        高质量调整视频尺寸
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出视频文件路径
            width: 目标宽度
            height: 目标高度
        """
        try:
            (
                ffmpeg
                .input(input_path) # type: ignore
                .filter("scale", width, height, flags="lanczos")
                .output(
                    os.path.splitext(input_path)[0]+output_path,
                    vcodec="libx264",
                    preset="veryslow",
                    crf=18,
                    acodec="copy"  # 直接复制音频流，不重新编码
                )
                .run()
            )
            print(f"成功调整视频尺寸: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"调整视频尺寸失败: {e}")
            raise
    
    def crop_video(self, input_path: str,x: int, y: int, 
                   width: int, height: int,
                   output_path: str='ouutput.mp4') -> None:
        """
        裁剪视频区域
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出视频文件路径
            x: 裁剪区域左上角x坐标
            y: 裁剪区域左上角y坐标
            width: 裁剪区域宽度
            height: 裁剪区域高度
        """
        try:
            (
                ffmpeg
                .input(input_path) # type: ignore
                .filter("crop", width, height, x, y)
                .output(
                    os.path.splitext(input_path)[0]+output_path,
                    vcodec="libx264",
                    preset="veryslow",
                    crf=18,
                    acodec="copy"
                )
                .run()
            )
            print(f"成功裁剪视频: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"裁剪视频失败: {e}")
            raise
    
    def video_to_gif(self, input_path: str, output_path: str='opt.gif', 
                    fps: int = 15,width: int = 500) -> None:
        """
        将视频转换为高质量GIF
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出GIF文件路径
            fps: 输出GIF的帧率
            scale: 输出GIF的高度，-1表示保持宽高比
            width: 输出GIF的宽度
        """
        try:
            # 计算高度以保持宽高比
            probe = ffmpeg.probe(input_path) # type: ignore
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("找不到视频流")
            
            input_width = int(video_stream['width'])
            input_height = int(video_stream['height'])
            height = int(input_height * width / input_width)
            
            # 生成调色板以提高GIF质量
            palette_path = os.path.splitext(input_path)[0]+output_path+".palette.png"
            
            # 生成调色板
            (
                ffmpeg
                .input(input_path) # type: ignore
                .filter("scale", width, height)
                .filter("fps", fps=fps)
                .filter("palettegen", stats_mode="full")
                .output(palette_path, loglevel="error")
                .run()
            )
            
            # 使用调色板生成GIF
            (
                ffmpeg
                .filter([ # type: ignore
                    ffmpeg.input(input_path).filter("scale", width, height).filter("fps", fps=fps), # type: ignore
                    ffmpeg.input(palette_path) # type: ignore
                ], "paletteuse", dither="bayer", bayer_scale=5)
                .output(os.path.splitext(input_path)[0]+output_path,loglevel="error")
                .run()
            )
            
            # 删除临时调色板文件
            if os.path.exists(palette_path):
                os.remove(palette_path)
                
            print(f"成功转换为GIF: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"转换为GIF失败: {e}")
            raise
    
    def add_watermark(self, input_path: str, 
                     watermark_path: str,  output_path: str='oopt.mp4',
                     position: str = "top-right", 
                     opacity: float = 0.7) -> None:
        """
        为视频添加水印
        
        Args:
            input_path: 输入视频文件路径
            output_path: 输出视频文件路径
            watermark_path: 水印图片路径
            position: 水印位置，可选值: top-left, top-right, bottom-left, bottom-right
            opacity: 水印透明度，范围0.0-1.0
        """
        try:
            # 确定水印位置
            if position == "top-left":
                x, y = "10", "10"
            elif position == "top-right":
                x, y = "main_w-overlay_w-10", "10"
            elif position == "bottom-left":
                x, y = "10", "main_h-overlay_h-10"
            elif position == "bottom-right":
                x, y = "main_w-overlay_w-10", "main_h-overlay_h-10"
            else:
                raise ValueError(f"未知的水印位置: {position}")
            
            # 加载视频和水印
            video = ffmpeg.input(input_path) # type: ignore
            watermark = ffmpeg.input(watermark_path).filter("format", "rgba") # type: ignore
            
            # 调整水印透明度
            watermark = watermark.filter("colorchannelmixer", aa=opacity)
            
            # 叠加水印
            output = ffmpeg.overlay(video, watermark, x=x, y=y) # type: ignore
            
            # 输出视频
            (
                output
                .output(
                    os.path.splitext(input_path)[0]+output_path,
                    vcodec="libx264",
                    preset="veryslow",
                    crf=18,
                    acodec="copy"
                )
                .run()
            )
            
            print(f"成功添加水印: {input_path} -> {output_path}")
        except Exception as e: # type: ignore
            print(f"添加水印失败: {e}")
            raise
    
    def get_video_info(self, input_path: str) -> dict:
        """
        获取视频文件信息
        
        Args:
            input_path: 输入视频文件路径
        
        Returns:
            包含视频信息的字典
        """
        try:
            return ffmpeg.probe(input_path) # type: ignore
        except Exception as e: # type: ignore
            print(f"获取视频信息失败: {e}")
            return  # pyright: ignore[reportReturnType]