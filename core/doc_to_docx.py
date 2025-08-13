# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import os
from win32com import client
#import time
import multiprocessing 

#print('''
    我们日常收到的好多资料是.doc.ppt.xls的，一个个点开另存为太麻烦，
    然而在忽略细微的兼容差异下，这种转换可以显著降低储存空间占用。
       ''')


def doc_to_docx(path):
        word = client.Dispatch('Word.Application')
        doc = word.Documents.Open(path)  # 目标路径下的文件
        doc.SaveAs(os.path.splitext(path)[0]+".docx", 16)  # 转化后路径下的文件
        doc.Close()
        word.Quit()
        #time.sleep(1) 
def xls_to_xlsx(path):
        excel = client.Dispatch('Excel.Application')
        xls = excel.Workbooks.Open(path)  # 目标路径下的文件
        xls.SaveAs(os.path.splitext(path)[0]+".xlsx", 51)  # 转化后路径下的文件
        xls.Close()
        excel.Quit()
        #time.sleep(1)
def ppt_to_pptx(path):
        powerpoint = client.Dispatch('PowerPoint.Application')
        client.gencache.EnsureDispatch('PowerPoint.Application') # type: ignore
        powerpoint.Visible=1
        ppt = powerpoint.Presentations.Open(path)  # 目标路径下的文件
        ppt.SaveAs(os.path.splitext(path)[0]+".pptx")  # 转化后路径下的文件
        ppt.Close()
        powerpoint.Quit()
        #time.sleep(1)
# def find_file(path, ext, file_list=[]):#在你提供的代码中，重复内容的问题源于
#  Python 函数默认参数的特性。当你将可变对象（如列表）作为默认参数时，这个【对象】在
# 函数定义时就会被创建，并且在每次调用函数时都会使用同一个【实例】。这意味着如果你多
# 次调用find_file函数而"不显式提供file_list参数"，之前调用的结果会被保留，导致重复。
def find_file(dir, ext, file_list=[]): 
    for i in dir:
        if ext == os.path.splitext(i)[1]:
            file_list.append(i)
    return file_list
#print(dir_path)
#os._exit()

def p3(dir_path):
    ext = ".doc"
    file_list = find_file(dir_path, ext,[])
    file_list.extend(find_file(dir_path,'.wps',[]))
    for file in file_list:
        try:
            doc_to_docx(file)
        except Exception as bcnr:
            #print("可接受异常:",bcnr)
#print(file_list)
def p1(dir_path):
    ext = ".xls"
    file_list = find_file(dir_path, ext,[])
    for file in file_list:
        try:
            xls_to_xlsx(file)
        except Exception as bcnr:
            #print("可接受异常:",bcnr)   
#print(file_list) 
def p2(dir_path):
    ext = ".ppt"
    file_list = find_file(dir_path, ext,[])
    for file in file_list:
        try:
            ppt_to_pptx(file)
        except Exception as bcnr:
            #print("可接受异常:",bcnr)
def begin(dir_path):

    # 定义要执行的任务列表，每个任务是一个元组：(函数, 参数列表)
    tasks = [
        (p1,dir_path),
        (p2,dir_path),
        (p3,dir_path)
    ]
    # 创建并启动进程
    processes = []
    for func, args in tasks:
        p = multiprocessing.Process(target=func, args=(args,))
        processes.append(p)
        p.start()
    #print("程序开始！")
    #print('等待所有进程完成')
    for p in processes:
        p.join()
    #print("finish\n为了安全，请验证输出结果后手动删除原文件。")