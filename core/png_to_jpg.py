# coding:utf-8
'''
        Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
        http://license.coscl.org.cn/MulanPSL2
'''
q={'.avif': 'AVIF', '.avifs': 'AVIF', '.blp': 'BLP', '.bmp': 'BMP', 
   '.dib': 'DIB', '.bufr': 'BUFR', '.cur': 'CUR', '.pcx': 'PCX', 
   '.dcx': 'DCX', '.dds': 'DDS', '.ps': 'EPS', '.eps': 'EPS', 
   '.fit': 'FITS', '.fits': 'FITS', '.fli': 'FLI', '.flc': 'FLI',
     '.ftc': 'FTEX', '.ftu': 'FTEX', '.gbr': 'GBR', '.gif': 'GIF', 
     '.grib': 'GRIB', '.h5': 'HDF5', '.hdf': 'HDF5', '.png': 'PNG', 
     '.apng': 'PNG', '.jp2': 'JPEG2000', '.j2k': 'JPEG2000', '.jpc': 
     'JPEG2000', '.jpf': 'JPEG2000', '.jpx': 'JPEG2000',
       '.j2c': 'JPEG2000', '.icns': 'ICNS', '.ico': 'ICO', '.im': 'IM',
         '.iim': 'IPTC', '.jfif': 'JPEG', '.jpe': 'JPEG', '.jpg': 'JPEG', 
         '.jpeg': 'JPEG', '.mpg': 'MPEG', '.mpeg': 'MPEG', '.tif': 'TIFF', 
         '.tiff': 'TIFF', '.mpo': 'MPO', '.msp': 'MSP', '.palm': 'PALM',
           '.pcd': 'PCD', '.pdf': 'PDF', '.pxr': 'PIXAR', '.pbm': 'PPM',
             '.pgm': 'PPM', '.ppm': 'PPM', '.pnm': 'PPM', '.pfm': 'PPM',
               '.psd': 'PSD', '.qoi': 'QOI', '.bw': 'SGI', '.rgb': 'SGI',
                 '.rgba': 'SGI', '.sgi': 'SGI', '.ras': 'SUN', 
                 '.tga': 'TGA', '.icb': 'TGA', '.vda': 'TGA',
                   '.vst': 'TGA', '.webp': 'WEBP', '.wmf': 'WMF',
                     '.emf': 'WMF', '.xbm': 'XBM', '.xpm': 'XPM'}
from PIL import Image
def begin(inp,form):
    with Image.open(inp)as i:
        try:  
            i.save(f'{inp}output{form}',q[form])
        except:
            # try:
            if form=='.xbm':
                rgb_img = i.convert('L') 
            elif form=='.blp':
                rgb_img = i.convert('P')
            else:
                rgb_img = i.convert('RGB') 
                # print(f"无法直接转换，尝试图像模式: {rgb_img.mode}")
            rgb_img.save(f'{inp}output.{form}',form)        
            # except Exception as e:
                # print(f"发生错误: {e}")
# begin(r"D:\Users\Easy\Downloads\容器.png",'.qoi')