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
def get_path(relative_path):
        try:
            base_path = os.path.dirname(sys.executables) # pyright: ignore[reportAttributeAccessIssue] # pyinstaller打包后的路径
            #注意和其他的不同,要获取exe所在文件夹.
        except AttributeError:
            base_path = os.path.abspath(".") # 当前工作目录的路径
        return os.path.normpath(os.path.join(base_path, relative_path))

def ffmpg(
         # 使用原始字符串避免转义问题
        arg0 = None,
        arg1 = None,
        arg2 = None,
        arg3 = None,
        arg4 = None,
        arg5 = None,
        exe_path =get_path('fmpegg.exe')
    ):

    command = f'{exe_path} {arg0} "{arg1}" "{arg2}" {arg3} {arg4} {arg5}'
    # if arg0==0 or arg0==1 or arg0==6:
    # # 拼接命令字符串
    #     command = f'{exe_path} {arg0} "{arg1}"'  # 用双引号包裹路径和参数，处理空格
    # elif arg0==8 or arg0==9:
    # # 拼接命令字符串
    #     command = f'{exe_path} {arg0} "{arg1}" "{arg2}"'
    # elif arg0==2 or arg0==4:
    # # 拼接命令字符串
    #     command = f'{exe_path} {arg0} "{arg1}" {arg2} {arg3}'
    # elif arg0==5 or arg0==7:
    # # 拼接命令字符串
    #     command = f'{exe_path} {arg0} "{arg1}" "{arg2}" {arg3} {arg4}'
    # else:
    # # 拼接命令字符串
    #     command = f'{exe_path} {arg0} "{arg1}" {arg2} {arg3} {arg4} {arg5}'
    #print(command)
    #print('正在执行……')
    os.system(command)
