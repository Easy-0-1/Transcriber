# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import pyecharts.options as opts
from pyecharts.charts import WordCloud
import jieba
import ctypes
from ctypes import wintypes

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

def c(wordDict,cut,rg,shape):
    s,b=map(int,rg)
    data = wordDict.items()
    if cut:
        a=[]
        for i in list(data):
            for j in range(int(i[1])):
                a.append(i[0])
        wl=[]
        for content in a:
            words = jieba.lcut(content)
            wl += words
        wordDict = {}
        for word in wl:
            if word == ".." or word == "......" or len(word) <= 1:
                continue
                # 如果该元素不存在字典的键中
            if word not in wordDict.keys():  
                    # 将字典中键所对应的值设置为1
                    wordDict[word] = 1
                # 否则
            else:
                    # 将字典中键所对应的值累加
                    wordDict[word] = wordDict[word] + 1
        wordCloud=WordCloud()
        wordCloud.add(series_name = "", data_pair = wordDict.items(), word_size_range = (s,b),width=900,height=500,shape =shape).set_global_opts( # pyright: ignore[reportArgumentType]
            # 标题设置
            title_opts=opts.TitleOpts(
                title="Easy Transcriber", title_textstyle_opts=opts.TextStyleOpts(font_size=20)
            ),
            # 提示框设置
            tooltip_opts=opts.TooltipOpts(is_show=True),
        ).render(get_desktop_path()+"\\wordcloud.html")
    
    else:
        _= (
            WordCloud()
            .add(
                # 系列名称，用于 tooltip 的显示，legend 的图例筛选。
                series_name="", 
                
                # 系列数据项，[(word1, count1), (word2, count2)]
                data_pair=data, # pyright: ignore[reportArgumentType]
                
                # 单词字体大小范围
                word_size_range = (s,b),width=800,height=500, # pyright: ignore[reportArgumentType]
                # 词云图轮廓，有 'circle', 'cardioid', 'diamond', 'triangle-forward', 'triangle', 'pentagon', 'star' 可选
                shape =shape
                
                )     
        # 全局配置项
        .set_global_opts(
            # 标题设置
            title_opts=opts.TitleOpts(
                title="Easy Transcriber", title_textstyle_opts=opts.TextStyleOpts(font_size=20)
            ),
            # 提示框设置
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
        .render(get_desktop_path()+"\\wordcloud.html")
    )
    #print('上述内容是与开发相关的提示，可以忽略。')
   # print('已保存在桌面，请重命名以免被覆写。')
   # print('在浏览器打开，每次点击刷新可变换排布样式。')
# c({'竹外桃花三两之':12,
#    '春江水暖一下子':19,
#    '白云深处有人家合成两千五 有三秋桂子，十里荷花':21,
#    " print('上述内容是与开发相关的提示，可以忽略。')print('已保存在桌面，请重命名以免被覆写。'print('在浏览器打开，每次点击刷新可变换排布样式。')":76,
#    '飞卢直下三千尺，疑是银河落九天':22,
#    '无边落木萧萧下，不尽长江滚滚来':25,
#    '月亮湾啼霜满天，江枫渔火对愁眠':31,
#    '飞来山上千寻塔，闻说鸡鸣见日升':23,
#    '落木千山田园大，澄江一道月分明':23,
#    '岑夫子丹丘生将进酒杯莫停':28,
#    '蒹葭苍苍，在河之洲，窈窕淑女，君子好逑':21,
#    '策扶老以流憩，抚孤松而盘桓':23,
#    '高余冠之岌岌兮，长于佩之陆离':25},1,(29,79),'circle')

