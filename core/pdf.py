# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
import pymupdf
def addimg(img,pdf,r):
    doc = pymupdf.open()                     # new PDF
    imgdoc=pymupdf.open(img)           # open image as a document
    pdfbytes=imgdoc.convert_to_pdf()  # make a 1-page PDF of it
    imgpdf=pymupdf.open("pdf", pdfbytes)
    doc.insert_pdf(imgpdf)             # insert the image PDF
    # doc.save('uuu.pdf')#如果要保存水印PDF，打开。
    docq = pymupdf.open(pdf)  
    for page in docq:
        page.show_pdf_page(rect = page.bound(),docsrc=doc,rotate=r,overlay=False) # pyright: ignore[reportAttributeAccessIssue]
    docq.save(pdf+'opt.pdf')
def gettext(pdf):
    doc = pymupdf.open(pdf) # open a document
    out = open(pdf+"output.doc", "w",encoding='utf-8') # create a text output
    #主要是txt同学可能不认识，docx不能直接写。
    for page in doc: # iterate the document pages
        text = page.get_text()  # pyright: ignore[reportAttributeAccessIssue] # get plain text (is in UTF-8)
        out.write(text) # write text of page
        out.write('\n\n\n\n\n') #换页
    out.write('若效果不佳，请使用图片识字功能。') # type: ignore
    out.close()
   # print('选择UTF-8编码打开输出文件。')
