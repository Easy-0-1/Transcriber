# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''

import sys
args = sys.argv[1:]
print(args)
if __name__ == "__main__":
    # 示例用法
    if args[0] in ('0','1','2','3','4','5','6','7','8'):
        print('有的方法处理后视频可能没声，可以提取原视频声音，再与新视频合成。')
        import ffmpegg # pyright: ignore[reportMissingImports]
        fffmpeg = ffmpegg.FFmpegUtils() 
        if args[0]=='0':
            print('H.264视频转换到H.265编码能在减少细微兼容性的情况下节省内存。')
            # #压缩视频
            fffmpeg.convert_to_h265(args[1])
        elif args[0]=='1': 
            # # 提取音频
            fffmpeg.extract_audio(args[1])
        elif args[0]=='2':   
            # 调整视频尺寸
            fffmpeg.resize_video(args[1],int(args[2]), int(args[3]))
        elif args[0]=='3': 
            # 裁剪视频
            fffmpeg.crop_video(args[1], int(args[2]),int(args[3]),int(args[4]),int(args[5]))
        elif args[0]=='4': 
            # 视频转GIF
            fffmpeg.video_to_gif(args[1], fps=int(args[2]), width=int(args[3]))
        elif args[0]=='5': 
            # 添加水印
            fffmpeg.add_watermark(args[1],args[2],position= args[3], opacity=int(args[4]))
        elif args[0]=='6': 
            # 获取视频信息
            info = fffmpeg.get_video_info(args[1])
            print(info)   
        elif args[0]=='7': 
            #转帧
            print('操作时间长，请耐心等待。')
            fffmpeg.fps(args[1],int(args[2]),m=args[3],w=args[4])
        elif args[0]=='8': 
            #音视频合流
            fffmpeg.together(args[1],args[2])
        print('请重命名output文件以免被覆写。')
    elif args[0]=='9':
        print('若出现繁体，可切换大模型试试')
        import abstract_voice # pyright: ignore[reportMissingImports]
        g=abstract_voice.g()
        g.g(args[1],args[2])
    print("程序运行完毕，按任意键退出...\n如需保存结果，从此窗口复制……")
    input()
    