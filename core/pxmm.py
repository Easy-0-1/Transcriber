# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import os

#若不行，用下面的（比较不安全）
#path=eval(input('文件路径是:'))
#获取该目录下所有文件，存入列表中
def begin(fileList,p,h:str):
    n=0
    for i in fileList:   
        #设置旧文件名（就是路径+文件名  
        path= os.path.dirname(i) # os.sep添加系统分隔符 
        #设置新文件名
        newname=path + os.sep +p+str(n+1)+h+os.path.splitext(i)[1]
        os.rename(i,newname)   #用os模块中的rename方法对文件改名
        print(os.path.basename(i),'======>',p+str(n+1)+h+os.path.splitext(i)[1])
        n+=1
# begin([r"D:\qqq.py"],'ahhhh','yyy')