# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
# 没有声音，注意
# 主要解决加字幕问题，很多软件这方面要收费
# 至于声音，很多软件都可以免费添加上去，就不重复造轮子了

import cv2
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import ast
def check_opencl_available():
    """检查OpenCL是否可用"""
    return cv2.ocl.haveOpenCL()

def add_subtitles(input_video, output_video, subtitles, use_gpu=True):
    """
    给视频添加字幕
    
    参数:
    input_video (str): 输入视频文件路径
    output_video (str): 输出视频文件路径
    subtitles (list): 字幕列表，每个字幕是一个字典，包含开始时间、结束时间和文本
    use_gpu (bool): 是否使用GPU加速
    """
    if use_gpu:
        if check_opencl_available():
            cv2.ocl.setUseOpenCL(True)  # 启用OpenCL
            #print("使用OpenCL进行GPU加速")
        else:
            #print("警告: OpenCL不可用，将使用CPU渲染")
            use_gpu = False

    # 打开视频文件
    cap = cv2.VideoCapture(input_video)
    
    if not cap.isOpened():
        #print(f"错误: 无法打开视频文件 {input_video}")
        return
    
    # 获取视频的帧率和尺寸
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 确保输出文件是.mp4扩展名
    if not output_video.lower().endswith('.mp4'):
        output_video += '.mp4'
        #print(f"注意: 输出文件已更改为: {output_video}")
    
    # 定义视频编码器并创建输出视频对象
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # pyright: ignore[reportAttributeAccessIssue] # 使用更通用的mp4v编码
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    if not out.isOpened():
        #print(f"错误: 无法创建输出视频文件 {output_video}")
        cap.release()
        return
    
    # 字幕位置和样式
    font_scale = 1
    color = (255, 255, 255)  # 白色
    thickness = 2
    
    # 计算字幕的垂直位置（底部上方一定距离）
    vertical_position = height - 50
    
    # 尝试加载支持中文的字体
    pil_font = None
    try:
        # 尝试不同的中文字体路径，根据系统不同可能需要调整
        font_path = None
        
        # 检查Windows字体路径
        if os.name == 'nt' and os.path.exists("C:/Windows/Fonts/simhei.ttf"):
            font_path = "C:/Windows/Fonts/simhei.ttf"
        # 检查Linux字体路径
        elif os.name == 'posix' and os.path.exists("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"):
            font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        # 检查macOS字体路径
        elif os.name == 'posix' and os.path.exists("/System/Library/Fonts/PingFang.ttc"):
            font_path = "/System/Library/Fonts/PingFang.ttc"
        
        if font_path:
            # 根据视频分辨率设置字体大小
            def get_font_size(video_width):
                if video_width >= 3840:  # 4K
                    return 72
                elif video_width >= 2560:  # 2K
                    return 48
                elif video_width >= 1920:  # 1080p
                    return 36
                else:  # 720p及以下
                    return 28

            # 使用示例
            font_size = get_font_size(width)  #
            pil_font = ImageFont.truetype(font_path, int(font_size * font_scale))
            #print(f"已加载中文字体: {font_path}")
        else:
            #print("警告: 未找到中文字体，将使用默认字体")
            pass
    except Exception as e:
        pass
        #print(f"加载字体时出错: {e}")
        #print("将使用默认字体，可能无法正确显示中文")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 计算当前帧对应的时间（秒）
        current_time = frame_count / fps
        
        # 检查当前时间是否在某个字幕的时间范围内
        current_subtitle = None
        for subtitle in subtitles:
            start_time = subtitle['start_time']
            end_time = subtitle['end_time']
            if start_time <= current_time <= end_time:
                current_subtitle = subtitle['text']
                break
        
        # 如果有当前字幕，则添加到帧上
        if current_subtitle:
            if pil_font:
                # 使用PIL绘制中文
                # 将OpenCV的BGR格式转换为RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame).convert("RGBA")
                draw = ImageDraw.Draw(pil_img)
                
                # 使用textbbox获取文本边界框，返回(x0, y0, x1, y1)
                bbox = draw.textbbox((0, 0), current_subtitle, font=pil_font)
                text_width = bbox[2] - bbox[0]  # 宽度 = 右边界 - 左边界
                text_height = bbox[3] - bbox[1]  # 高度 = 下边界 - 上边界
                horizontal_position = (width - text_width) // 2
                
                # 背景框参数
                background_color = (0, 0, 0,100)  # 黑色背景
                background_padding = 10
                background_x = horizontal_position - background_padding
                background_y = vertical_position - text_height - background_padding
                background_width = text_width + 2 * background_padding
                background_height = text_height + 2 * background_padding
                
                # 添加背景
                draw.rectangle([(background_x, background_y), 
                               (background_x + background_width, background_y + background_height)], 
                               fill=background_color)
                
                # 添加文字
                draw.text((horizontal_position, vertical_position - text_height), 
                         current_subtitle, font=pil_font, fill=color)
                
                # 转回BGR格式
                rgba_array = np.array(pil_img)
                rgb_array = rgba_array[:, :, :3]  # RGB部分
                alpha_array = rgba_array[:, :, 3]  # Alpha部分
                
                # 创建带Alpha通道的OpenCV图像
                bgr = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
                bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
                bgra[:, :, 3] = alpha_array  # 设置Alpha通道

                # 将带透明度的图像与原始帧混合
                mask = alpha_array[:, :, np.newaxis].astype(np.float32) / 255.0
                frame = (bgra[:, :, :3] * mask + frame * (1 - mask)).astype(np.uint8)
            else:
                # 使用OpenCV默认字体（可能不支持中文）
                (text_width, text_height), _ = cv2.getTextSize(current_subtitle, 
                                                              cv2.FONT_HERSHEY_SIMPLEX, 
                                                              font_scale, thickness)
                horizontal_position = (width - text_width) // 2
                
                # 创建背景框（半透明）
                background_color = (0, 0, 0)  # BGR格式的黑色
                background_padding = 10
                alpha = 0.4  # 透明度值：0.0（完全透明）到1.0（完全不透明）

                # 创建一个与当前帧相同的副本
                overlay = frame.copy()

                # 绘制背景框（在副本上）
                cv2.rectangle(overlay, 
                            (horizontal_position - background_padding, vertical_position - text_height - background_padding),
                            (horizontal_position + text_width + background_padding, vertical_position + background_padding),
                            background_color, -1)  # -1表示填充矩形

                # 将副本与原始帧按alpha比例混合
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                
                # 添加文字
                cv2.putText(frame, current_subtitle, (horizontal_position, vertical_position), 
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
        
        # 写入帧到输出视频
        out.write(frame)
        frame_count += 1
    
    # 释放资源（移到循环外部）
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    #print(f"成功处理 {frame_count} 帧")
    #print(f"字幕已添加到视频: {output_video}")

# def time_to_seconds(time_str):
#     """将HH:MM:SS格式的时间转换为秒"""
#     time_obj = datetime.strptime(time_str, '%H:%M:%S')
#     delta = timedelta(hours=time_obj.hour, minutes=time_obj.minute, seconds=time_obj.second)
#     return delta.total_seconds()

def main(input_video,subtitles):    
    # 示例字幕数据
    try:
        subtitles = ast.literal_eval('['+subtitles+']')  # 仅解析字面量
        #Caution: A complex expression can overflow the C stack and cause a crash.                    
    except Exception as e:
        pass
        #print(f"格式错误：{e}")
    # {'start_time': 12.9, 'end_time': 14.26, 'text': 'drew'} ,
    # {'start_time': 16.36, 'end_time': 20.46, 'text': 'vvvvvvv'} ,
    # {'start_time': 25.04, 'end_time': 26.8, 'text': '2'} ,
    # {'start_time': 30.0, 'end_time': 32.0, 'text': '我看你不就说了吗'} ,
    # {'start_time': 32.0, 'end_time': 34.0, 'text': '你不就说了吗'} ,
    # {'start_time': 34.0, 'end_time': 36.0, 'text': '他突然间一看老师'} ,
    # {'start_time': 36.0, 'end_time': 38.0, 'text': '我也很棒'} ,
    # {'start_time': 38.0, 'end_time': 40.0, 'text': '他一直问我现在几点'} ,
    # {'start_time': 40.0, 'end_time': 42.0, 'text': '我昨天有做错些什么'} ,
    # {'start_time': 42.0, 'end_time': 44.0, 'text': '他就跟着说'} ,
    # {'start_time': 44.0, 'end_time': 46.0, 'text': '我说我昨天有做错些什么'} ,
    # {'start_time': 46.0, 'end_time': 48.0, 'text': '他就跟着说'} ,
    # {'start_time': 48.0, 'end_time': 50.0, 'text': '你跟他聊一下'} ,
    # {'start_time': 50.0, 'end_time': 52.0, 'text': '给他一种未知感'} ,
    # {'start_time': 52.0, 'end_time': 54.0, 'text': '对啊他跟着说'} ,
    # {'start_time': 54.0, 'end_time': 56.0, 'text': '然后就一直这样'} ,
    # {'start_time': 56.0, 'end_time': 58.0, 'text': '然后他跟他一起来'} ,
    # {'start_time': 58.0, 'end_time': 60.0, 'text': '我们那个大爷'} ,
    # {'start_time': 60.0, 'end_time': 62.0, 'text': '我不说话他说话'} ,
    
    
    # 添加字幕到视频
    output_video = input_video+'output_with_subtitles.mp4'
    
    if not os.path.exists(input_video):
        #print(f"错误: 输入视频文件不存在: {input_video}")
        return
    
    add_subtitles(input_video, output_video, subtitles)
    #print(f"字幕已成功添加到视频！输出文件: {output_video}")
    #print('如果没声音，可使用提取音频，音视频合流功能。')
 