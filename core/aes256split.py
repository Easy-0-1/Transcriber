# -*- coding: utf-8 -*-
'''
Copyright (c) 2025 Easy
Easy Transcriber is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
    http://license.coscl.org.cn/MulanPSL2
'''

print('''
注意！本加密方法与网上的AES不兼容！
网上的在线解密工具未能还原由这里加密形成的密文！
具体原因有待分析。
正式场合使用时应合理评估此加密方法安全性！
''')

import os
os.environ["PYOPENCL_COMPILER_OUTPUT"] = "1"  # 启用编译器输出
import pyopencl as cl  # 必须在设置环境变量后导入 pyopencl
import numpy as np
import time

# OpenCL内核代码，使用T表优化
#我感觉不兼容可能的原因就是T表的问题，因为1.网上解密出来段落，换行和各段的字量
#与原文是一致的，只是具体文字变乱码。2.AES的各步骤我都基本能知道大体形式和过程
#就是那样，唯有T表生成比较抽象晦涩，网上和文献中没有现成的可以用，至于生成方式
#问了三个AI各说各的，我指出和文献不一致，它们马上改口，第二天又说我的不对，可是
#他们自己说的过几天我再问他们也说这样不对。
#此外，计数器生成逻辑有差异，向量化可能有其他问题也可能导致不兼容，但是能力有限，
#无法排查清除。
opencl_kernel = """
// AES常量定义
#define N_ROUNDS 14
#define BLOCK_SIZE 16
#define AES_ROUND(state_vec, round_idx) \
    do { \
        uint4 t0 = T[(state_vec.x >> 24) & 0xFF]; \
        uint4 t1 = T[(state_vec.y >> 16) & 0xFF]; \
        uint4 t2 = T[(state_vec.z >> 8) & 0xFF]; \
        uint4 t3 = T[state_vec.w & 0xFF]; \
        \
        uint4 round_key = vload4(0, &words[4 * (round_idx + 1)]); \
        state_vec = (uint4)( \
            t0.x ^ t1.y ^ t2.z ^ t3.w ^ round_key.x, \
            t0.y ^ t1.z ^ t2.w ^ t3.x ^ round_key.y, \
            t0.z ^ t1.w ^ t2.x ^ t3.y ^ round_key.z, \
            t0.w ^ t1.x ^ t2.y ^ t3.z ^ round_key.w \
        ); \
    } while (0)
#define SUBWORD(x) ((Te4[(x>>24)&0xFF]<<24) | (Te4[(x>>16)&0xFF]<<16) | \
                    (Te4[(x>>8)&0xFF]<<8)  | (Te4[(x)&0xFF]))
#define ROTWORD(x) ((x) << 8 | (x) >> 24)

// 轮常量 (RCON) 
__constant unsigned int rcon[14] = {0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 
    0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D}; 
// S盒 (SubBytes操作) 
//__constant unsigned char s_box[256] = { 0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76, 0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15, 0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75, 0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84, 0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf, 0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8, 0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73, 0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb, 0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79, 0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08, 0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a, 0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e, 0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf, 0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16 }; 
// T表 (预计算的SubBytes+ShiftRows+MixColumns)
__constant uint4 T[256] = {
    (uint4)(0xc66363a5, 0xa5c66363, 0x63a5c663, 0x6363a5c6),
    (uint4)(0xf87c7c84, 0x84f87c7c, 0x7c84f87c, 0x7c7c84f8),
    (uint4)(0xee777799, 0x99ee7777, 0x7799ee77, 0x777799ee),
    (uint4)(0xf67b7b8d, 0x8df67b7b, 0x7b8df67b, 0x7b7b8df6),
    (uint4)(0xfff2f20d, 0x0dfff2f2, 0xf20dfff2, 0xf2f20dff),
    (uint4)(0xd66b6bbd, 0xbdd66b6b, 0x6bbdd66b, 0x6b6bbdd6),
    (uint4)(0xde6f6fb1, 0xb1de6f6f, 0x6fb1de6f, 0x6f6fb1de),
    (uint4)(0x91c5c554, 0x5491c5c5, 0xc55491c5, 0xc5c55491),
    (uint4)(0x60303050, 0x50603030, 0x30506030, 0x30305060),
    (uint4)(0x02010103, 0x03020101, 0x01030201, 0x01010302),
    (uint4)(0xce6767a9, 0xa9ce6767, 0x67a9ce67, 0x6767a9ce),
    (uint4)(0x562b2b7d, 0x7d562b2b, 0x2b7d562b, 0x2b2b7d56),
    (uint4)(0xe7fefe19, 0x19e7fefe, 0xfe19e7fe, 0xfefe19e7),
    (uint4)(0xb5d7d762, 0x62b5d7d7, 0xd762b5d7, 0xd7d762b5),
    (uint4)(0x4dababe6, 0xe64dabab, 0xabe64dab, 0xababe64d),
    (uint4)(0xec76769a, 0x9aec7676, 0x769aec76, 0x76769aec),
    (uint4)(0x8fcaca45, 0x458fcaca, 0xca458fca, 0xcaca458f),
    (uint4)(0x1f82829d, 0x9d1f8282, 0x829d1f82, 0x82829d1f),
    (uint4)(0x89c9c940, 0x4089c9c9, 0xc94089c9, 0xc9c94089),
    (uint4)(0xfa7d7d87, 0x87fa7d7d, 0x7d87fa7d, 0x7d7d87fa),
    (uint4)(0xeffafa15, 0x15effafa, 0xfa15effa, 0xfafa15ef),
    (uint4)(0xb25959eb, 0xebb25959, 0x59ebb259, 0x5959ebb2),
    (uint4)(0x8e4747c9, 0xc98e4747, 0x47c98e47, 0x4747c98e),
    (uint4)(0xfbf0f00b, 0x0bfbf0f0, 0xf00bfbf0, 0xf0f00bfb),
    (uint4)(0x41adadec, 0xec41adad, 0xadec41ad, 0xadadec41),
    (uint4)(0xb3d4d467, 0x67b3d4d4, 0xd467b3d4, 0xd4d467b3),
    (uint4)(0x5fa2a2fd, 0xfd5fa2a2, 0xa2fd5fa2, 0xa2a2fd5f),
    (uint4)(0x45afafea, 0xea45afaf, 0xafea45af, 0xafafea45),
    (uint4)(0x239c9cbf, 0xbf239c9c, 0x9cbf239c, 0x9c9cbf23),
    (uint4)(0x53a4a4f7, 0xf753a4a4, 0xa4f753a4, 0xa4a4f753),
    (uint4)(0xe4727296, 0x96e47272, 0x7296e472, 0x727296e4),
    (uint4)(0x9bc0c05b, 0x5b9bc0c0, 0xc05b9bc0, 0xc0c05b9b),
    (uint4)(0x75b7b7c2, 0xc275b7b7, 0xb7c275b7, 0xb7b7c275),
    (uint4)(0xe1fdfd1c, 0x1ce1fdfd, 0xfd1ce1fd, 0xfdfd1ce1),
    (uint4)(0x3d9393ae, 0xae3d9393, 0x93ae3d93, 0x9393ae3d),
    (uint4)(0x4c26266a, 0x6a4c2626, 0x266a4c26, 0x26266a4c),
    (uint4)(0x6c36365a, 0x5a6c3636, 0x365a6c36, 0x36365a6c),
    (uint4)(0x7e3f3f41, 0x417e3f3f, 0x3f417e3f, 0x3f3f417e),
    (uint4)(0xf5f7f702, 0x02f5f7f7, 0xf702f5f7, 0xf7f702f5),
    (uint4)(0x83cccc4f, 0x4f83cccc, 0xcc4f83cc, 0xcccc4f83),
    (uint4)(0x6834345c, 0x5c683434, 0x345c6834, 0x34345c68),
    (uint4)(0x51a5a5f4, 0xf451a5a5, 0xa5f451a5, 0xa5a5f451),
    (uint4)(0xd1e5e534, 0x34d1e5e5, 0xe534d1e5, 0xe5e534d1),
    (uint4)(0xf9f1f108, 0x08f9f1f1, 0xf108f9f1, 0xf1f108f9),
    (uint4)(0xe2717193, 0x93e27171, 0x7193e271, 0x717193e2),
    (uint4)(0xabd8d873, 0x73abd8d8, 0xd873abd8, 0xd8d873ab),
    (uint4)(0x62313153, 0x53623131, 0x31536231, 0x31315362),
    (uint4)(0x2a15153f, 0x3f2a1515, 0x153f2a15, 0x15153f2a),
    (uint4)(0x0804040c, 0x0c080404, 0x040c0804, 0x04040c08),
    (uint4)(0x95c7c752, 0x5295c7c7, 0xc75295c7, 0xc7c75295),
    (uint4)(0x46232365, 0x65462323, 0x23654623, 0x23236546),
    (uint4)(0x9dc3c35e, 0x5e9dc3c3, 0xc35e9dc3, 0xc3c35e9d),
    (uint4)(0x30181828, 0x28301818, 0x18283018, 0x18182830),
    (uint4)(0x379696a1, 0xa1379696, 0x96a13796, 0x9696a137),
    (uint4)(0x0a05050f, 0x0f0a0505, 0x050f0a05, 0x05050f0a),
    (uint4)(0x2f9a9ab5, 0xb52f9a9a, 0x9ab52f9a, 0x9a9ab52f),
    (uint4)(0x0e070709, 0x090e0707, 0x07090e07, 0x0707090e),
    (uint4)(0x24121236, 0x36241212, 0x12362412, 0x12123624),
    (uint4)(0x1b80809b, 0x9b1b8080, 0x809b1b80, 0x80809b1b),
    (uint4)(0xdfe2e23d, 0x3ddfe2e2, 0xe23ddfe2, 0xe2e23ddf),
    (uint4)(0xcdebeb26, 0x26cdebeb, 0xeb26cdeb, 0xebeb26cd),
    (uint4)(0x4e272769, 0x694e2727, 0x27694e27, 0x2727694e),
    (uint4)(0x7fb2b2cd, 0xcd7fb2b2, 0xb2cd7fb2, 0xb2b2cd7f),
    (uint4)(0xea75759f, 0x9fea7575, 0x759fea75, 0x75759fea),
    (uint4)(0x1209091b, 0x1b120909, 0x091b1209, 0x09091b12),
    (uint4)(0x1d83839e, 0x9e1d8383, 0x839e1d83, 0x83839e1d),
    (uint4)(0x582c2c74, 0x74582c2c, 0x2c74582c, 0x2c2c7458),
    (uint4)(0x341a1a2e, 0x2e341a1a, 0x1a2e341a, 0x1a1a2e34),
    (uint4)(0x361b1b2d, 0x2d361b1b, 0x1b2d361b, 0x1b1b2d36),
    (uint4)(0xdc6e6eb2, 0xb2dc6e6e, 0x6eb2dc6e, 0x6e6eb2dc),
    (uint4)(0xb45a5aee, 0xeeb45a5a, 0x5aeeb45a, 0x5a5aeeb4),
    (uint4)(0x5ba0a0fb, 0xfb5ba0a0, 0xa0fb5ba0, 0xa0a0fb5b),
    (uint4)(0xa45252f6, 0xf6a45252, 0x52f6a452, 0x5252f6a4),
    (uint4)(0x763b3b4d, 0x4d763b3b, 0x3b4d763b, 0x3b3b4d76),
    (uint4)(0xb7d6d661, 0x61b7d6d6, 0xd661b7d6, 0xd6d661b7),
    (uint4)(0x7db3b3ce, 0xce7db3b3, 0xb3ce7db3, 0xb3b3ce7d),
    (uint4)(0x5229297b, 0x7b522929, 0x297b5229, 0x29297b52),
    (uint4)(0xdde3e33e, 0x3edde3e3, 0xe33edde3, 0xe3e33edd),
    (uint4)(0x5e2f2f71, 0x715e2f2f, 0x2f715e2f, 0x2f2f715e),
    (uint4)(0x13848497, 0x97138484, 0x84971384, 0x84849713),
    (uint4)(0xa65353f5, 0xf5a65353, 0x53f5a653, 0x5353f5a6),
    (uint4)(0xb9d1d168, 0x68b9d1d1, 0xd168b9d1, 0xd1d168b9),
    (uint4)(0x00000000, 0x00000000, 0x00000000, 0x00000000),
    (uint4)(0xc1eded2c, 0x2cc1eded, 0xed2cc1ed, 0xeded2cc1),
    (uint4)(0x40202060, 0x60402020, 0x20604020, 0x20206040),
    (uint4)(0xe3fcfc1f, 0x1fe3fcfc, 0xfc1fe3fc, 0xfcfc1fe3),
    (uint4)(0x79b1b1c8, 0xc879b1b1, 0xb1c879b1, 0xb1b1c879),
    (uint4)(0xb65b5bed, 0xedb65b5b, 0x5bedb65b, 0x5b5bedb6),
    (uint4)(0xd46a6abe, 0xbed46a6a, 0x6abed46a, 0x6a6abed4),
    (uint4)(0x8dcbcb46, 0x468dcbcb, 0xcb468dcb, 0xcbcb468d),
    (uint4)(0x67bebed9, 0xd967bebe, 0xbed967be, 0xbebed967),
    (uint4)(0x7239394b, 0x4b723939, 0x394b7239, 0x39394b72),
    (uint4)(0x944a4ade, 0xde944a4a, 0x4ade944a, 0x4a4ade94),
    (uint4)(0x984c4cd4, 0xd4984c4c, 0x4cd4984c, 0x4c4cd498),
    (uint4)(0xb05858e8, 0xe8b05858, 0x58e8b058, 0x5858e8b0),
    (uint4)(0x85cfcf4a, 0x4a85cfcf, 0xcf4a85cf, 0xcfcf4a85),
    (uint4)(0xbbd0d06b, 0x6bbbd0d0, 0xd06bbbd0, 0xd0d06bbb),
    (uint4)(0xc5efef2a, 0x2ac5efef, 0xef2ac5ef, 0xefef2ac5),
    (uint4)(0x4faaaae5, 0xe54faaaa, 0xaae54faa, 0xaaaae54f),
    (uint4)(0xedfbfb16, 0x16edfbfb, 0xfb16edfb, 0xfbfb16ed),
    (uint4)(0x864343c5, 0xc5864343, 0x43c58643, 0x4343c586),
    (uint4)(0x9a4d4dd7, 0xd79a4d4d, 0x4dd79a4d, 0x4d4dd79a),
    (uint4)(0x66333355, 0x55663333, 0x33556633, 0x33335566),
    (uint4)(0x11858594, 0x94118585, 0x85941185, 0x85859411),
    (uint4)(0x8a4545cf, 0xcf8a4545, 0x45cf8a45, 0x4545cf8a),
    (uint4)(0xe9f9f910, 0x10e9f9f9, 0xf910e9f9, 0xf9f910e9),
    (uint4)(0x04020206, 0x06040202, 0x02060402, 0x02020604),
    (uint4)(0xfe7f7f81, 0x81fe7f7f, 0x7f81fe7f, 0x7f7f81fe),
    (uint4)(0xa05050f0, 0xf0a05050, 0x50f0a050, 0x5050f0a0),
    (uint4)(0x783c3c44, 0x44783c3c, 0x3c44783c, 0x3c3c4478),
    (uint4)(0x259f9fba, 0xba259f9f, 0x9fba259f, 0x9f9fba25),
    (uint4)(0x4ba8a8e3, 0xe34ba8a8, 0xa8e34ba8, 0xa8a8e34b),
    (uint4)(0xa25151f3, 0xf3a25151, 0x51f3a251, 0x5151f3a2),
    (uint4)(0x5da3a3fe, 0xfe5da3a3, 0xa3fe5da3, 0xa3a3fe5d),
    (uint4)(0x804040c0, 0xc0804040, 0x40c08040, 0x4040c080),
    (uint4)(0x058f8f8a, 0x8a058f8f, 0x8f8a058f, 0x8f8f8a05),
    (uint4)(0x3f9292ad, 0xad3f9292, 0x92ad3f92, 0x9292ad3f),
    (uint4)(0x219d9dbc, 0xbc219d9d, 0x9dbc219d, 0x9d9dbc21),
    (uint4)(0x70383848, 0x48703838, 0x38487038, 0x38384870),
    (uint4)(0xf1f5f504, 0x04f1f5f5, 0xf504f1f5, 0xf5f504f1),
    (uint4)(0x63bcbcdf, 0xdf63bcbc, 0xbcdf63bc, 0xbcbcdf63),
    (uint4)(0x77b6b6c1, 0xc177b6b6, 0xb6c177b6, 0xb6b6c177),
    (uint4)(0xafdada75, 0x75afdada, 0xda75afda, 0xdada75af),
    (uint4)(0x42212163, 0x63422121, 0x21634221, 0x21216342),
    (uint4)(0x20101030, 0x30201010, 0x10302010, 0x10103020),
    (uint4)(0xe5ffff1a, 0x1ae5ffff, 0xff1ae5ff, 0xffff1ae5),
    (uint4)(0xfdf3f30e, 0x0efdf3f3, 0xf30efdf3, 0xf3f30efd),
    (uint4)(0xbfd2d26d, 0x6dbfd2d2, 0xd26dbfd2, 0xd2d26dbf),
    (uint4)(0x81cdcd4c, 0x4c81cdcd, 0xcd4c81cd, 0xcdcd4c81),
    (uint4)(0x180c0c14, 0x14180c0c, 0x0c14180c, 0x0c0c1418),
    (uint4)(0x26131335, 0x35261313, 0x13352613, 0x13133526),
    (uint4)(0xc3ecec2f, 0x2fc3ecec, 0xec2fc3ec, 0xecec2fc3),
    (uint4)(0xbe5f5fe1, 0xe1be5f5f, 0x5fe1be5f, 0x5f5fe1be),
    (uint4)(0x359797a2, 0xa2359797, 0x97a23597, 0x9797a235),
    (uint4)(0x884444cc, 0xcc884444, 0x44cc8844, 0x4444cc88),
    (uint4)(0x2e171739, 0x392e1717, 0x17392e17, 0x1717392e),
    (uint4)(0x93c4c457, 0x5793c4c4, 0xc45793c4, 0xc4c45793),
    (uint4)(0x55a7a7f2, 0xf255a7a7, 0xa7f255a7, 0xa7a7f255),
    (uint4)(0xfc7e7e82, 0x82fc7e7e, 0x7e82fc7e, 0x7e7e82fc),
    (uint4)(0x7a3d3d47, 0x477a3d3d, 0x3d477a3d, 0x3d3d477a),
    (uint4)(0xc86464ac, 0xacc86464, 0x64acc864, 0x6464acc8),
    (uint4)(0xba5d5de7, 0xe7ba5d5d, 0x5de7ba5d, 0x5d5de7ba),
    (uint4)(0x3219192b, 0x2b321919, 0x192b3219, 0x19192b32),
    (uint4)(0xe6737395, 0x95e67373, 0x7395e673, 0x737395e6),
    (uint4)(0xc06060a0, 0xa0c06060, 0x60a0c060, 0x6060a0c0),
    (uint4)(0x19818198, 0x98198181, 0x81981981, 0x81819819),
    (uint4)(0x9e4f4fd1, 0xd19e4f4f, 0x4fd19e4f, 0x4f4fd19e),
    (uint4)(0xa3dcdc7f, 0x7fa3dcdc, 0xdc7fa3dc, 0xdcdc7fa3),
    (uint4)(0x44222266, 0x66442222, 0x22664422, 0x22226644),
    (uint4)(0x542a2a7e, 0x7e542a2a, 0x2a7e542a, 0x2a2a7e54),
    (uint4)(0x3b9090ab, 0xab3b9090, 0x90ab3b90, 0x9090ab3b),
    (uint4)(0x0b888883, 0x830b8888, 0x88830b88, 0x8888830b),
    (uint4)(0x8c4646ca, 0xca8c4646, 0x46ca8c46, 0x4646ca8c),
    (uint4)(0xc7eeee29, 0x29c7eeee, 0xee29c7ee, 0xeeee29c7),
    (uint4)(0x6bb8b8d3, 0xd36bb8b8, 0xb8d36bb8, 0xb8b8d36b),
    (uint4)(0x2814143c, 0x3c281414, 0x143c2814, 0x14143c28),
    (uint4)(0xa7dede79, 0x79a7dede, 0xde79a7de, 0xdede79a7),
    (uint4)(0xbc5e5ee2, 0xe2bc5e5e, 0x5ee2bc5e, 0x5e5ee2bc),
    (uint4)(0x160b0b1d, 0x1d160b0b, 0x0b1d160b, 0x0b0b1d16),
    (uint4)(0xaddbdb76, 0x76addbdb, 0xdb76addb, 0xdbdb76ad),
    (uint4)(0xdbe0e03b, 0x3bdbe0e0, 0xe03bdbe0, 0xe0e03bdb),
    (uint4)(0x64323256, 0x56643232, 0x32566432, 0x32325664),
    (uint4)(0x743a3a4e, 0x4e743a3a, 0x3a4e743a, 0x3a3a4e74),
    (uint4)(0x140a0a1e, 0x1e140a0a, 0x0a1e140a, 0x0a0a1e14),
    (uint4)(0x924949db, 0xdb924949, 0x49db9249, 0x4949db92),
    (uint4)(0x0c06060a, 0x0a0c0606, 0x060a0c06, 0x06060a0c),
    (uint4)(0x4824246c, 0x6c482424, 0x246c4824, 0x24246c48),
    (uint4)(0xb85c5ce4, 0xe4b85c5c, 0x5ce4b85c, 0x5c5ce4b8),
    (uint4)(0x9fc2c25d, 0x5d9fc2c2, 0xc25d9fc2, 0xc2c25d9f),
    (uint4)(0xbdd3d36e, 0x6ebdd3d3, 0xd36ebdd3, 0xd3d36ebd),
    (uint4)(0x43acacef, 0xef43acac, 0xacef43ac, 0xacacef43),
    (uint4)(0xc46262a6, 0xa6c46262, 0x62a6c462, 0x6262a6c4),
    (uint4)(0x399191a8, 0xa8399191, 0x91a83991, 0x9191a839),
    (uint4)(0x319595a4, 0xa4319595, 0x95a43195, 0x9595a431),
    (uint4)(0xd3e4e437, 0x37d3e4e4, 0xe437d3e4, 0xe4e437d3),
    (uint4)(0xf279798b, 0x8bf27979, 0x798bf279, 0x79798bf2),
    (uint4)(0xd5e7e732, 0x32d5e7e7, 0xe732d5e7, 0xe7e732d5),
    (uint4)(0x8bc8c843, 0x438bc8c8, 0xc8438bc8, 0xc8c8438b),
    (uint4)(0x6e373759, 0x596e3737, 0x37596e37, 0x3737596e),
    (uint4)(0xda6d6db7, 0xb7da6d6d, 0x6db7da6d, 0x6d6db7da),
    (uint4)(0x018d8d8c, 0x8c018d8d, 0x8d8c018d, 0x8d8d8c01),
    (uint4)(0xb1d5d564, 0x64b1d5d5, 0xd564b1d5, 0xd5d564b1),
    (uint4)(0x9c4e4ed2, 0xd29c4e4e, 0x4ed29c4e, 0x4e4ed29c),
    (uint4)(0x49a9a9e0, 0xe049a9a9, 0xa9e049a9, 0xa9a9e049),
    (uint4)(0xd86c6cb4, 0xb4d86c6c, 0x6cb4d86c, 0x6c6cb4d8),
    (uint4)(0xac5656fa, 0xfaac5656, 0x56faac56, 0x5656faac),
    (uint4)(0xf3f4f407, 0x07f3f4f4, 0xf407f3f4, 0xf4f407f3),
    (uint4)(0xcfeaea25, 0x25cfeaea, 0xea25cfea, 0xeaea25cf),
    (uint4)(0xca6565af, 0xafca6565, 0x65afca65, 0x6565afca),
    (uint4)(0xf47a7a8e, 0x8ef47a7a, 0x7a8ef47a, 0x7a7a8ef4),
    (uint4)(0x47aeaee9, 0xe947aeae, 0xaee947ae, 0xaeaee947),
    (uint4)(0x10080818, 0x18100808, 0x08181008, 0x08081810),
    (uint4)(0x6fbabad5, 0xd56fbaba, 0xbad56fba, 0xbabad56f),
    (uint4)(0xf0787888, 0x88f07878, 0x7888f078, 0x787888f0),
    (uint4)(0x4a25256f, 0x6f4a2525, 0x256f4a25, 0x25256f4a),
    (uint4)(0x5c2e2e72, 0x725c2e2e, 0x2e725c2e, 0x2e2e725c),
    (uint4)(0x381c1c24, 0x24381c1c, 0x1c24381c, 0x1c1c2438),
    (uint4)(0x57a6a6f1, 0xf157a6a6, 0xa6f157a6, 0xa6a6f157),
    (uint4)(0x73b4b4c7, 0xc773b4b4, 0xb4c773b4, 0xb4b4c773),
    (uint4)(0x97c6c651, 0x5197c6c6, 0xc65197c6, 0xc6c65197),
    (uint4)(0xcbe8e823, 0x23cbe8e8, 0xe823cbe8, 0xe8e823cb),
    (uint4)(0xa1dddd7c, 0x7ca1dddd, 0xdd7ca1dd, 0xdddd7ca1),
    (uint4)(0xe874749c, 0x9ce87474, 0x749ce874, 0x74749ce8),
    (uint4)(0x3e1f1f21, 0x213e1f1f, 0x1f213e1f, 0x1f1f213e),
    (uint4)(0x964b4bdd, 0xdd964b4b, 0x4bdd964b, 0x4b4bdd96),
    (uint4)(0x61bdbddc, 0xdc61bdbd, 0xbddc61bd, 0xbdbddc61),
    (uint4)(0x0d8b8b86, 0x860d8b8b, 0x8b860d8b, 0x8b8b860d),
    (uint4)(0x0f8a8a85, 0x850f8a8a, 0x8a850f8a, 0x8a8a850f),
    (uint4)(0xe0707090, 0x90e07070, 0x7090e070, 0x707090e0),
    (uint4)(0x7c3e3e42, 0x427c3e3e, 0x3e427c3e, 0x3e3e427c),
    (uint4)(0x71b5b5c4, 0xc471b5b5, 0xb5c471b5, 0xb5b5c471),
    (uint4)(0xcc6666aa, 0xaacc6666, 0x66aacc66, 0x6666aacc),
    (uint4)(0x904848d8, 0xd8904848, 0x48d89048, 0x4848d890),
    (uint4)(0x06030305, 0x05060303, 0x03050603, 0x03030506),
    (uint4)(0xf7f6f601, 0x01f7f6f6, 0xf601f7f6, 0xf6f601f7),
    (uint4)(0x1c0e0e12, 0x121c0e0e, 0x0e121c0e, 0x0e0e121c),
    (uint4)(0xc26161a3, 0xa3c26161, 0x61a3c261, 0x6161a3c2),
    (uint4)(0x6a35355f, 0x5f6a3535, 0x355f6a35, 0x35355f6a),
    (uint4)(0xae5757f9, 0xf9ae5757, 0x57f9ae57, 0x5757f9ae),
    (uint4)(0x69b9b9d0, 0xd069b9b9, 0xb9d069b9, 0xb9b9d069),
    (uint4)(0x17868691, 0x91178686, 0x86911786, 0x86869117),
    (uint4)(0x99c1c158, 0x5899c1c1, 0xc15899c1, 0xc1c15899),
    (uint4)(0x3a1d1d27, 0x273a1d1d, 0x1d273a1d, 0x1d1d273a),
    (uint4)(0x279e9eb9, 0xb9279e9e, 0x9eb9279e, 0x9e9eb927),
    (uint4)(0xd9e1e138, 0x38d9e1e1, 0xe138d9e1, 0xe1e138d9),
    (uint4)(0xebf8f813, 0x13ebf8f8, 0xf813ebf8, 0xf8f813eb),
    (uint4)(0x2b9898b3, 0xb32b9898, 0x98b32b98, 0x9898b32b),
    (uint4)(0x22111133, 0x33221111, 0x11332211, 0x11113322),
    (uint4)(0xd26969bb, 0xbbd26969, 0x69bbd269, 0x6969bbd2),
    (uint4)(0xa9d9d970, 0x70a9d9d9, 0xd970a9d9, 0xd9d970a9),
    (uint4)(0x078e8e89, 0x89078e8e, 0x8e89078e, 0x8e8e8907),
    (uint4)(0x339494a7, 0xa7339494, 0x94a73394, 0x9494a733),
    (uint4)(0x2d9b9bb6, 0xb62d9b9b, 0x9bb62d9b, 0x9b9bb62d),
    (uint4)(0x3c1e1e22, 0x223c1e1e, 0x1e223c1e, 0x1e1e223c),
    (uint4)(0x15878792, 0x92158787, 0x87921587, 0x87879215),
    (uint4)(0xc9e9e920, 0x20c9e9e9, 0xe920c9e9, 0xe9e920c9),
    (uint4)(0x87cece49, 0x4987cece, 0xce4987ce, 0xcece4987),
    (uint4)(0xaa5555ff, 0xffaa5555, 0x55ffaa55, 0x5555ffaa),
    (uint4)(0x50282878, 0x78502828, 0x28785028, 0x28287850),
    (uint4)(0xa5dfdf7a, 0x7aa5dfdf, 0xdf7aa5df, 0xdfdf7aa5),
    (uint4)(0x038c8c8f, 0x8f038c8c, 0x8c8f038c, 0x8c8c8f03),
    (uint4)(0x59a1a1f8, 0xf859a1a1, 0xa1f859a1, 0xa1a1f859),
    (uint4)(0x09898980, 0x80098989, 0x89800989, 0x89898009),
    (uint4)(0x1a0d0d17, 0x171a0d0d, 0x0d171a0d, 0x0d0d171a),
    (uint4)(0x65bfbfda, 0xda65bfbf, 0xbfda65bf, 0xbfbfda65),
    (uint4)(0xd7e6e631, 0x31d7e6e6, 0xe631d7e6, 0xe6e631d7),
    (uint4)(0x844242c6, 0xc6844242, 0x42c68442, 0x4242c684),
    (uint4)(0xd06868b8, 0xb8d06868, 0x68b8d068, 0x6868b8d0),
    (uint4)(0x824141c3, 0xc3824141, 0x41c38241, 0x4141c382),
    (uint4)(0x299999b0, 0xb0299999, 0x99b02999, 0x9999b029),
    (uint4)(0x5a2d2d77, 0x775a2d2d, 0x2d775a2d, 0x2d2d775a),
    (uint4)(0x1e0f0f11, 0x111e0f0f, 0x0f111e0f, 0x0f0f111e),
    (uint4)(0x7bb0b0cb, 0xcb7bb0b0, 0xb0cb7bb0, 0xb0b0cb7b),
    (uint4)(0xa85454fc, 0xfca85454, 0x54fca854, 0x5454fca8),
    (uint4)(0x6dbbbbd6, 0xd66dbbbb, 0xbbd66dbb, 0xbbbbd66d),
    (uint4)(0x2c16163a, 0x3a2c1616, 0x163a2c16, 0x16163a2c),
};
__constant uint4 T4_uint4[256] = {
    (uint4)(0x63636363, 0x63636363, 0x63636363, 0x63636363),
    (uint4)(0x7c7c7c7c, 0x7c7c7c7c, 0x7c7c7c7c, 0x7c7c7c7c),
    (uint4)(0x77777777, 0x77777777, 0x77777777, 0x77777777),
    (uint4)(0x7b7b7b7b, 0x7b7b7b7b, 0x7b7b7b7b, 0x7b7b7b7b),
    (uint4)(0xf2f2f2f2, 0xf2f2f2f2, 0xf2f2f2f2, 0xf2f2f2f2),
    (uint4)(0x6b6b6b6b, 0x6b6b6b6b, 0x6b6b6b6b, 0x6b6b6b6b),
    (uint4)(0x6f6f6f6f, 0x6f6f6f6f, 0x6f6f6f6f, 0x6f6f6f6f),
    (uint4)(0xc5c5c5c5, 0xc5c5c5c5, 0xc5c5c5c5, 0xc5c5c5c5),
    (uint4)(0x30303030, 0x30303030, 0x30303030, 0x30303030),
    (uint4)(0x01010101, 0x01010101, 0x01010101, 0x01010101),
    (uint4)(0x67676767, 0x67676767, 0x67676767, 0x67676767),
    (uint4)(0x2b2b2b2b, 0x2b2b2b2b, 0x2b2b2b2b, 0x2b2b2b2b),
    (uint4)(0xfefefefe, 0xfefefefe, 0xfefefefe, 0xfefefefe),
    (uint4)(0xd7d7d7d7, 0xd7d7d7d7, 0xd7d7d7d7, 0xd7d7d7d7),
    (uint4)(0xabababab, 0xabababab, 0xabababab, 0xabababab),
    (uint4)(0x76767676, 0x76767676, 0x76767676, 0x76767676),
    (uint4)(0xcacaacac, 0xcacaacac, 0xcacaacac, 0xcacaacac),
    (uint4)(0x82828282, 0x82828282, 0x82828282, 0x82828282),
    (uint4)(0xc9c9c9c9, 0xc9c9c9c9, 0xc9c9c9c9, 0xc9c9c9c9),
    (uint4)(0x7d7d7d7d, 0x7d7d7d7d, 0x7d7d7d7d, 0x7d7d7d7d),
    (uint4)(0xfafafafa, 0xfafafafa, 0xfafafafa, 0xfafafafa),
    (uint4)(0x59595959, 0x59595959, 0x59595959, 0x59595959),
    (uint4)(0x47474747, 0x47474747, 0x47474747, 0x47474747),
    (uint4)(0xf0f0f0f0, 0xf0f0f0f0, 0xf0f0f0f0, 0xf0f0f0f0),
    (uint4)(0xadadadad, 0xadadadad, 0xadadadad, 0xadadadad),
    (uint4)(0xd4d4d4d4, 0xd4d4d4d4, 0xd4d4d4d4, 0xd4d4d4d4),
    (uint4)(0xa2a2a2a2, 0xa2a2a2a2, 0xa2a2a2a2, 0xa2a2a2a2),
    (uint4)(0xafafafaf, 0xafafafaf, 0xafafafaf, 0xafafafaf),
    (uint4)(0x9c9c9c9c, 0x9c9c9c9c, 0x9c9c9c9c, 0x9c9c9c9c),
    (uint4)(0xa4a4a4a4, 0xa4a4a4a4, 0xa4a4a4a4, 0xa4a4a4a4),
    (uint4)(0x72727272, 0x72727272, 0x72727272, 0x72727272),
    (uint4)(0xc0c0c0c0, 0xc0c0c0c0, 0xc0c0c0c0, 0xc0c0c0c0),
    (uint4)(0xb7b7b7b7, 0xb7b7b7b7, 0xb7b7b7b7, 0xb7b7b7b7),
    (uint4)(0xfdfdfdfd, 0xfdfdfdfd, 0xfdfdfdfd, 0xfdfdfdfd),
    (uint4)(0x93939393, 0x93939393, 0x93939393, 0x93939393),
    (uint4)(0x26262626, 0x26262626, 0x26262626, 0x26262626),
    (uint4)(0x36363636, 0x36363636, 0x36363636, 0x36363636),
    (uint4)(0x3f3f3f3f, 0x3f3f3f3f, 0x3f3f3f3f, 0x3f3f3f3f),
    (uint4)(0xf7f7f7f7, 0xf7f7f7f7, 0xf7f7f7f7, 0xf7f7f7f7),
    (uint4)(0xcccccccc, 0xcccccccc, 0xcccccccc, 0xcccccccc),
    (uint4)(0x34343434, 0x34343434, 0x34343434, 0x34343434),
    (uint4)(0xa5a5a5a5, 0xa5a5a5a5, 0xa5a5a5a5, 0xa5a5a5a5),
    (uint4)(0xe5e5e5e5, 0xe5e5e5e5, 0xe5e5e5e5, 0xe5e5e5e5),
    (uint4)(0xf1f1f1f1, 0xf1f1f1f1, 0xf1f1f1f1, 0xf1f1f1f1),
    (uint4)(0x71717171, 0x71717171, 0x71717171, 0x71717171),
    (uint4)(0xd8d8d8d8, 0xd8d8d8d8, 0xd8d8d8d8, 0xd8d8d8d8),
    (uint4)(0x31313131, 0x31313131, 0x31313131, 0x31313131),
    (uint4)(0x15151515, 0x15151515, 0x15151515, 0x15151515),
    (uint4)(0x04040404, 0x04040404, 0x04040404, 0x04040404),
    (uint4)(0xc7c7c7c7, 0xc7c7c7c7, 0xc7c7c7c7, 0xc7c7c7c7),
    (uint4)(0x23232323, 0x23232323, 0x23232323, 0x23232323),
    (uint4)(0xc3c3c3c3, 0xc3c3c3c3, 0xc3c3c3c3, 0xc3c3c3c3),
    (uint4)(0x18181818, 0x18181818, 0x18181818, 0x18181818),
    (uint4)(0x96969696, 0x96969696, 0x96969696, 0x96969696),
    (uint4)(0x05050505, 0x05050505, 0x05050505, 0x05050505),
    (uint4)(0x9a9a9a9a, 0x9a9a9a9a, 0x9a9a9a9a, 0x9a9a9a9a),
    (uint4)(0x07070707, 0x07070707, 0x07070707, 0x07070707),
    (uint4)(0x12121212, 0x12121212, 0x12121212, 0x12121212),
    (uint4)(0x80808080, 0x80808080, 0x80808080, 0x80808080),
    (uint4)(0xe2e2e2e2, 0xe2e2e2e2, 0xe2e2e2e2, 0xe2e2e2e2),
    (uint4)(0xebebebeb, 0xebebebeb, 0xebebebeb, 0xebebebeb),
    (uint4)(0x27272727, 0x27272727, 0x27272727, 0x27272727),
    (uint4)(0xb2b2b2b2, 0xb2b2b2b2, 0xb2b2b2b2, 0xb2b2b2b2),
    (uint4)(0x75757575, 0x75757575, 0x75757575, 0x75757575),
    (uint4)(0x09090909, 0x09090909, 0x09090909, 0x09090909),
    (uint4)(0x83838383, 0x83838383, 0x83838383, 0x83838383),
    (uint4)(0x2c2c2c2c, 0x2c2c2c2c, 0x2c2c2c2c, 0x2c2c2c2c),
    (uint4)(0x1a1a1a1a, 0x1a1a1a1a, 0x1a1a1a1a, 0x1a1a1a1a),
    (uint4)(0x1b1b1b1b, 0x1b1b1b1b, 0x1b1b1b1b, 0x1b1b1b1b),
    (uint4)(0x6e6e6e6e, 0x6e6e6e6e, 0x6e6e6e6e, 0x6e6e6e6e),
    (uint4)(0x5a5a5a5a, 0x5a5a5a5a, 0x5a5a5a5a, 0x5a5a5a5a),
    (uint4)(0xa0a0a0a0, 0xa0a0a0a0, 0xa0a0a0a0, 0xa0a0a0a0),
    (uint4)(0x52525252, 0x52525252, 0x52525252, 0x52525252),
    (uint4)(0x3b3b3b3b, 0x3b3b3b3b, 0x3b3b3b3b, 0x3b3b3b3b),
    (uint4)(0xd6d6d6d6, 0xd6d6d6d6, 0xd6d6d6d6, 0xd6d6d6d6),
    (uint4)(0xb3b3b3b3, 0xb3b3b3b3, 0xb3b3b3b3, 0xb3b3b3b3),
    (uint4)(0x29292929, 0x29292929, 0x29292929, 0x29292929),
    (uint4)(0xe3e3e3e3, 0xe3e3e3e3, 0xe3e3e3e3, 0xe3e3e3e3),
    (uint4)(0x2f2f2f2f, 0x2f2f2f2f, 0x2f2f2f2f, 0x2f2f2f2f),
    (uint4)(0x84848484, 0x84848484, 0x84848484, 0x84848484),
    (uint4)(0x53535353, 0x53535353, 0x53535353, 0x53535353),
    (uint4)(0xd1d1d1d1, 0xd1d1d1d1, 0xd1d1d1d1, 0xd1d1d1d1),
    (uint4)(0x00000000, 0x00000000, 0x00000000, 0x00000000),
    (uint4)(0xededdede, 0xededdede, 0xededdede, 0xededdede),
    (uint4)(0x20202020, 0x20202020, 0x20202020, 0x20202020),
    (uint4)(0xfcfcfcfc, 0xfcfcfcfc, 0xfcfcfcfc, 0xfcfcfcfc),
    (uint4)(0xb1b1b1b1, 0xb1b1b1b1, 0xb1b1b1b1, 0xb1b1b1b1),
    (uint4)(0x5b5b5b5b, 0x5b5b5b5b, 0x5b5b5b5b, 0x5b5b5b5b),
    (uint4)(0x6a6a6a6a, 0x6a6a6a6a, 0x6a6a6a6a, 0x6a6a6a6a),
    (uint4)(0xcbcbcbcb, 0xcbcbcbcb, 0xcbcbcbcb, 0xcbcbcbcb),
    (uint4)(0xbebebebe, 0xbebebebe, 0xbebebebe, 0xbebebebe),
    (uint4)(0x39393939, 0x39393939, 0x39393939, 0x39393939),
    (uint4)(0x4a4a4a4a, 0x4a4a4a4a, 0x4a4a4a4a, 0x4a4a4a4a),
    (uint4)(0x4c4c4c4c, 0x4c4c4c4c, 0x4c4c4c4c, 0x4c4c4c4c),
    (uint4)(0x58585858, 0x58585858, 0x58585858, 0x58585858),
    (uint4)(0xcfcfcfcf, 0xcfcfcfcf, 0xcfcfcfcf, 0xcfcfcfcf),
    (uint4)(0xd0d0d0d0, 0xd0d0d0d0, 0xd0d0d0d0, 0xd0d0d0d0),
    (uint4)(0xefefefef, 0xefefefef, 0xefefefef, 0xefefefef),
    (uint4)(0xaaaaaaaa, 0xaaaaaaaa, 0xaaaaaaaa, 0xaaaaaaaa),
    (uint4)(0xfbfbfbfb, 0xfbfbfbfb, 0xfbfbfbfb, 0xfbfbfbfb),
    (uint4)(0x43434343, 0x43434343, 0x43434343, 0x43434343),
    (uint4)(0x4d4d4d4d, 0x4d4d4d4d, 0x4d4d4d4d, 0x4d4d4d4d),
    (uint4)(0x33333333, 0x33333333, 0x33333333, 0x33333333),
    (uint4)(0x85858585, 0x85858585, 0x85858585, 0x85858585),
    (uint4)(0x45454545, 0x45454545, 0x45454545, 0x45454545),
    (uint4)(0xf9f9f9f9, 0xf9f9f9f9, 0xf9f9f9f9, 0xf9f9f9f9),
    (uint4)(0x02020202, 0x02020202, 0x02020202, 0x02020202),
    (uint4)(0x7f7f7f7f, 0x7f7f7f7f, 0x7f7f7f7f, 0x7f7f7f7f),
    (uint4)(0x50505050, 0x50505050, 0x50505050, 0x50505050),
    (uint4)(0x3c3c3c3c, 0x3c3c3c3c, 0x3c3c3c3c, 0x3c3c3c3c),
    (uint4)(0x9f9f9f9f, 0x9f9f9f9f, 0x9f9f9f9f, 0x9f9f9f9f),
    (uint4)(0xa8a8a8a8, 0xa8a8a8a8, 0xa8a8a8a8, 0xa8a8a8a8),
    (uint4)(0x51515151, 0x51515151, 0x51515151, 0x51515151),
    (uint4)(0xa3a3a3a3, 0xa3a3a3a3, 0xa3a3a3a3, 0xa3a3a3a3),
    (uint4)(0x40404040, 0x40404040, 0x40404040, 0x40404040),
    (uint4)(0x8f8f8f8f, 0x8f8f8f8f, 0x8f8f8f8f, 0x8f8f8f8f),
    (uint4)(0x92929292, 0x92929292, 0x92929292, 0x92929292),
    (uint4)(0x9d9d9d9d, 0x9d9d9d9d, 0x9d9d9d9d, 0x9d9d9d9d),
    (uint4)(0x38383838, 0x38383838, 0x38383838, 0x38383838),
    (uint4)(0xf5f5f5f5, 0xf5f5f5f5, 0xf5f5f5f5, 0xf5f5f5f5),
    (uint4)(0xbcbcbcbc, 0xbcbcbcbc, 0xbcbcbcbc, 0xbcbcbcbc),
    (uint4)(0xb6b6b6b6, 0xb6b6b6b6, 0xb6b6b6b6, 0xb6b6b6b6),
    (uint4)(0xdadadada, 0xdadadada, 0xdadadada, 0xdadadada),
    (uint4)(0x21212121, 0x21212121, 0x21212121, 0x21212121),
    (uint4)(0x10101010, 0x10101010, 0x10101010, 0x10101010),
    (uint4)(0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff),
    (uint4)(0xf3f3f3f3, 0xf3f3f3f3, 0xf3f3f3f3, 0xf3f3f3f3),
    (uint4)(0xd2d2d2d2, 0xd2d2d2d2, 0xd2d2d2d2, 0xd2d2d2d2),
    (uint4)(0xcdcdcdcd, 0xcdcdcdcd, 0xcdcdcdcd, 0xcdcdcdcd),
    (uint4)(0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c),
    (uint4)(0x13131313, 0x13131313, 0x13131313, 0x13131313),
    (uint4)(0xecececec, 0xecececec, 0xecececec, 0xecececec),
    (uint4)(0x5f5f5f5f, 0x5f5f5f5f, 0x5f5f5f5f, 0x5f5f5f5f),
    (uint4)(0x97979797, 0x97979797, 0x97979797, 0x97979797),
    (uint4)(0x44444444, 0x44444444, 0x44444444, 0x44444444),
    (uint4)(0x17171717, 0x17171717, 0x17171717, 0x17171717),
    (uint4)(0xc4c4c4c4, 0xc4c4c4c4, 0xc4c4c4c4, 0xc4c4c4c4),
    (uint4)(0xa7a7a7a7, 0xa7a7a7a7, 0xa7a7a7a7, 0xa7a7a7a7),
    (uint4)(0x7e7e7e7e, 0x7e7e7e7e, 0x7e7e7e7e, 0x7e7e7e7e),
    (uint4)(0x3d3d3d3d, 0x3d3d3d3d, 0x3d3d3d3d, 0x3d3d3d3d),
    (uint4)(0x64646464, 0x64646464, 0x64646464, 0x64646464),
    (uint4)(0x5d5d5d5d, 0x5d5d5d5d, 0x5d5d5d5d, 0x5d5d5d5d),
    (uint4)(0x19191919, 0x19191919, 0x19191919, 0x19191919),
    (uint4)(0x73737373, 0x73737373, 0x73737373, 0x73737373),
    (uint4)(0x60606060, 0x60606060, 0x60606060, 0x60606060),
    (uint4)(0x81818181, 0x81818181, 0x81818181, 0x81818181),
    (uint4)(0x4f4f4f4f, 0x4f4f4f4f, 0x4f4f4f4f, 0x4f4f4f4f),
    (uint4)(0xdcdcbcdc, 0xdcdcbcdc, 0xdcdcbcdc, 0xdcdcbcdc),
    (uint4)(0x22222222, 0x22222222, 0x22222222, 0x22222222),
    (uint4)(0x2a2a2a2a, 0x2a2a2a2a, 0x2a2a2a2a, 0x2a2a2a2a),
    (uint4)(0x90909090, 0x90909090, 0x90909090, 0x90909090),
    (uint4)(0x88888888, 0x88888888, 0x88888888, 0x88888888),
    (uint4)(0x46464646, 0x46464646, 0x46464646, 0x46464646),
    (uint4)(0xeeeeeeee, 0xeeeeeeee, 0xeeeeeeee, 0xeeeeeeee),
    (uint4)(0xb8b8b8b8, 0xb8b8b8b8, 0xb8b8b8b8, 0xb8b8b8b8),
    (uint4)(0x14141414, 0x14141414, 0x14141414, 0x14141414),
    (uint4)(0xdededede, 0xdededede, 0xdededede, 0xdededede),
    (uint4)(0x5e5e5e5e, 0x5e5e5e5e, 0x5e5e5e5e, 0x5e5e5e5e),
    (uint4)(0x0b0b0b0b, 0x0b0b0b0b, 0x0b0b0b0b, 0x0b0b0b0b),
    (uint4)(0xdbdbdbdb, 0xdbdbdbdb, 0xdbdbdbdb, 0xdbdbdbdb),
    (uint4)(0xe0e0e0e0, 0xe0e0e0e0, 0xe0e0e0e0, 0xe0e0e0e0),
    (uint4)(0x32323232, 0x32323232, 0x32323232, 0x32323232),
    (uint4)(0x3a3a3a3a, 0x3a3a3a3a, 0x3a3a3a3a, 0x3a3a3a3a),
    (uint4)(0x0a0a0a0a, 0x0a0a0a0a, 0x0a0a0a0a, 0x0a0a0a0a),
    (uint4)(0x49494949, 0x49494949, 0x49494949, 0x49494949),
    (uint4)(0x06060606, 0x06060606, 0x06060606, 0x06060606),
    (uint4)(0x24242424, 0x24242424, 0x24242424, 0x24242424),
    (uint4)(0x5c5c5c5c, 0x5c5c5c5c, 0x5c5c5c5c, 0x5c5c5c5c),
    (uint4)(0xc2c2c2c2, 0xc2c2c2c2, 0xc2c2c2c2, 0xc2c2c2c2),
    (uint4)(0xd3d3d3d3, 0xd3d3d3d3, 0xd3d3d3d3, 0xd3d3d3d3),
    (uint4)(0xacacacac, 0xacacacac, 0xacacacac, 0xacacacac),
    (uint4)(0x62626262, 0x62626262, 0x62626262, 0x62626262),
    (uint4)(0x91919191, 0x91919191, 0x91919191, 0x91919191),
    (uint4)(0x95959595, 0x95959595, 0x95959595, 0x95959595),
    (uint4)(0xe4e4e4e4, 0xe4e4e4e4, 0xe4e4e4e4, 0xe4e4e4e4),
    (uint4)(0x79797979, 0x79797979, 0x79797979, 0x79797979),
    (uint4)(0xe7e7e7e7, 0xe7e7e7e7, 0xe7e7e7e7, 0xe7e7e7e7),
    (uint4)(0xc8c8c8c8, 0xc8c8c8c8, 0xc8c8c8c8, 0xc8c8c8c8),
    (uint4)(0x37373737, 0x37373737, 0x37373737, 0x37373737),
    (uint4)(0x6d6d6d6d, 0x6d6d6d6d, 0x6d6d6d6d, 0x6d6d6d6d),
    (uint4)(0x8d8d8d8d, 0x8d8d8d8d, 0x8d8d8d8d, 0x8d8d8d8d),
    (uint4)(0xd5d5d5d5, 0xd5d5d5d5, 0xd5d5d5d5, 0xd5d5d5d5),
    (uint4)(0x4e4e4e4e, 0x4e4e4e4e, 0x4e4e4e4e, 0x4e4e4e4e),
    (uint4)(0xa9a9a9a9, 0xa9a9a9a9, 0xa9a9a9a9, 0xa9a9a9a9),
    (uint4)(0x6c6c6c6c, 0x6c6c6c6c, 0x6c6c6c6c, 0x6c6c6c6c),
    (uint4)(0x56565656, 0x56565656, 0x56565656, 0x56565656),
    (uint4)(0xf4f4f4f4, 0xf4f4f4f4, 0xf4f4f4f4, 0xf4f4f4f4),
    (uint4)(0xeaeaeaea, 0xeaeaeaea, 0xeaeaeaea, 0xeaeaeaea),
    (uint4)(0x65656565, 0x65656565, 0x65656565, 0x65656565),
    (uint4)(0x7a7a7a7a, 0x7a7a7a7a, 0x7a7a7a7a, 0x7a7a7a7a),
    (uint4)(0xaeaeaeae, 0xaeaeaeae, 0xaeaeaeae, 0xaeaeaeae),
    (uint4)(0x08080808, 0x08080808, 0x08080808, 0x08080808),
    (uint4)(0xbabababa, 0xbabababa, 0xbabababa, 0xbabababa),
    (uint4)(0x78787878, 0x78787878, 0x78787878, 0x78787878),
    (uint4)(0x25252525, 0x25252525, 0x25252525, 0x25252525),
    (uint4)(0x2e2e2e2e, 0x2e2e2e2e, 0x2e2e2e2e, 0x2e2e2e2e),
    (uint4)(0x1c1c1c1c, 0x1c1c1c1c, 0x1c1c1c1c, 0x1c1c1c1c),
    (uint4)(0xa6a6a6a6, 0xa6a6a6a6, 0xa6a6a6a6, 0xa6a6a6a6),
    (uint4)(0xb4b4b4b4, 0xb4b4b4b4, 0xb4b4b4b4, 0xb4b4b4b4),
    (uint4)(0xc6c6c6c6, 0xc6c6c6c6, 0xc6c6c6c6, 0xc6c6c6c6),
    (uint4)(0xe8e8e8e8, 0xe8e8e8e8, 0xe8e8e8e8, 0xe8e8e8e8),
    (uint4)(0xdddddddd, 0xdddddddd, 0xdddddddd, 0xdddddddd),
    (uint4)(0x74747474, 0x74747474, 0x74747474, 0x74747474),
    (uint4)(0x1f1f1f1f, 0x1f1f1f1f, 0x1f1f1f1f, 0x1f1f1f1f),
    (uint4)(0x4b4b4b4b, 0x4b4b4b4b, 0x4b4b4b4b, 0x4b4b4b4b),
    (uint4)(0xbdbdbdbd, 0xbdbdbdbd, 0xbdbdbdbd, 0xbdbdbdbd),
    (uint4)(0x8b8b8b8b, 0x8b8b8b8b, 0x8b8b8b8b, 0x8b8b8b8b),
    (uint4)(0x8a8a8a8a, 0x8a8a8a8a, 0x8a8a8a8a, 0x8a8a8a8a),
    (uint4)(0x70707070, 0x70707070, 0x70707070, 0x70707070),
    (uint4)(0x3e3e3e3e, 0x3e3e3e3e, 0x3e3e3e3e, 0x3e3e3e3e),
    (uint4)(0xb5b5b5b5, 0xb5b5b5b5, 0xb5b5b5b5, 0xb5b5b5b5),
    (uint4)(0x66666666, 0x66666666, 0x66666666, 0x66666666),
    (uint4)(0x48484848, 0x48484848, 0x48484848, 0x48484848),
    (uint4)(0x03030303, 0x03030303, 0x03030303, 0x03030303),
    (uint4)(0xf6f6f6f6, 0xf6f6f6f6, 0xf6f6f6f6, 0xf6f6f6f6),
    (uint4)(0x0e0e0e0e, 0x0e0e0e0e, 0x0e0e0e0e, 0x0e0e0e0e),
    (uint4)(0x61616161, 0x61616161, 0x61616161, 0x61616161),
    (uint4)(0x35353535, 0x35353535, 0x35353535, 0x35353535),
    (uint4)(0x57575757, 0x57575757, 0x57575757, 0x57575757),
    (uint4)(0xb9b9b9b9, 0xb9b9b9b9, 0xb9b9b9b9, 0xb9b9b9b9),
    (uint4)(0x86868686, 0x86868686, 0x86868686, 0x86868686),
    (uint4)(0xc1c1c1c1, 0xc1c1c1c1, 0xc1c1c1c1, 0xc1c1c1c1),
    (uint4)(0x1d1d1d1d, 0x1d1d1d1d, 0x1d1d1d1d, 0x1d1d1d1d),
    (uint4)(0x9e9e9e9e, 0x9e9e9e9e, 0x9e9e9e9e, 0x9e9e9e9e),
    (uint4)(0xe1e1e1e1, 0xe1e1e1e1, 0xe1e1e1e1, 0xe1e1e1e1),
    (uint4)(0xf8f8f8f8, 0xf8f8f8f8, 0xf8f8f8f8, 0xf8f8f8f8),
    (uint4)(0x98989898, 0x98989898, 0x98989898, 0x98989898),
    (uint4)(0x11111111, 0x11111111, 0x11111111, 0x11111111),
    (uint4)(0x69696969, 0x69696969, 0x69696969, 0x69696969),
    (uint4)(0xd9d9d9d9, 0xd9d9d9d9, 0xd9d9d9d9, 0xd9d9d9d9),
    (uint4)(0x8e8e8e8e, 0x8e8e8e8e, 0x8e8e8e8e, 0x8e8e8e8e),
    (uint4)(0x94949494, 0x94949494, 0x94949494, 0x94949494),
    (uint4)(0x9b9b9b9b, 0x9b9b9b9b, 0x9b9b9b9b, 0x9b9b9b9b),
    (uint4)(0x1e1e1e1e, 0x1e1e1e1e, 0x1e1e1e1e, 0x1e1e1e1e),
    (uint4)(0x87878787, 0x87878787, 0x87878787, 0x87878787),
    (uint4)(0xe9e9e9e9, 0xe9e9e9e9, 0xe9e9e9e9, 0xe9e9e9e9),
    (uint4)(0xcececece, 0xcececece, 0xcececece, 0xcececece),
    (uint4)(0x55555555, 0x55555555, 0x55555555, 0x55555555),
    (uint4)(0x28282828, 0x28282828, 0x28282828, 0x28282828),
    (uint4)(0xdfdfdfdf, 0xdfdfdfdf, 0xdfdfdfdf, 0xdfdfdfdf),
    (uint4)(0x8c8c8c8c, 0x8c8c8c8c, 0x8c8c8c8c, 0x8c8c8c8c),
    (uint4)(0xa1a1a1a1, 0xa1a1a1a1, 0xa1a1a1a1, 0xa1a1a1a1),
    (uint4)(0x89898989, 0x89898989, 0x89898989, 0x89898989),
    (uint4)(0x0d0d0d0d, 0x0d0d0d0d, 0x0d0d0d0d, 0x0d0d0d0d),
    (uint4)(0xbfbfbfbf, 0xbfbfbfbf, 0xbfbfbfbf, 0xbfbfbfbf),
    (uint4)(0xe6e6e6e6, 0xe6e6e6e6, 0xe6e6e6e6, 0xe6e6e6e6),
    (uint4)(0x42424242, 0x42424242, 0x42424242, 0x42424242),
    (uint4)(0x68686868, 0x68686868, 0x68686868, 0x68686868),
    (uint4)(0x41414141, 0x41414141, 0x41414141, 0x41414141),
    (uint4)(0x99999999, 0x99999999, 0x99999999, 0x99999999),
    (uint4)(0x2d2d2d2d, 0x2d2d2d2d, 0x2d2d2d2d, 0x2d2d2d2d),
    (uint4)(0x0f0f0f0f, 0x0f0f0f0f, 0x0f0f0f0f, 0x0f0f0f0f),
    (uint4)(0xb0b0b0b0, 0xb0b0b0b0, 0xb0b0b0b0, 0xb0b0b0b0),
    (uint4)(0x54545454, 0x54545454, 0x54545454, 0x54545454),
    (uint4)(0xbbbbbbbb, 0xbbbbbbbb, 0xbbbbbbbb, 0xbbbbbbbb),
    (uint4)(0x16161616, 0x16161616, 0x16161616, 0x16161616),
};//仅包含 SubBytes（字节替换）的预计算

__constant uint Te4[256] = {
    0x63000000, 0x7C000000, 0x77000000, 0x7B000000, 0xF2000000, 0x6B000000, 0x6F000000, 0xC5000000,
    0x30000000, 0x01000000, 0x67000000, 0x2B000000, 0xFE000000, 0xD7000000, 0xAB000000, 0x76000000,
    0xCA000000, 0x82000000, 0xC9000000, 0x7D000000, 0xFA000000, 0x59000000, 0x47000000, 0xF0000000,
    0xAD000000, 0xD4000000, 0xA2000000, 0xAF000000, 0x9C000000, 0xA4000000, 0x72000000, 0xC0000000,
    0xB7000000, 0xFD000000, 0x93000000, 0x26000000, 0x36000000, 0x3F000000, 0xF7000000, 0xCC000000,
    0x34000000, 0xA5000000, 0xE5000000, 0xF1000000, 0x71000000, 0xD8000000, 0x31000000, 0x15000000,
    0x04000000, 0xC7000000, 0x23000000, 0xC3000000, 0x18000000, 0x96000000, 0x05000000, 0x9A000000,
    0x07000000, 0x12000000, 0x80000000, 0xE2000000, 0xEB000000, 0x27000000, 0xB2000000, 0x75000000,
    0x09000000, 0x83000000, 0x2C000000, 0x1A000000, 0x1B000000, 0x6E000000, 0x5A000000, 0xA0000000,
    0x52000000, 0x3B000000, 0xD6000000, 0xB3000000, 0x29000000, 0xE3000000, 0x2F000000, 0x84000000,
    0x53000000, 0xD1000000, 0x00000000, 0xED000000, 0x20000000, 0xFC000000, 0xB1000000, 0x5B000000,
    0x6A000000, 0xCB000000, 0xBE000000, 0x39000000, 0x4A000000, 0x4C000000, 0x58000000, 0xCF000000,
    0xD0000000, 0xEF000000, 0xAA000000, 0xFB000000, 0x43000000, 0x4D000000, 0x33000000, 0x85000000,
    0x45000000, 0xF9000000, 0x02000000, 0x7F000000, 0x50000000, 0x3C000000, 0x9F000000, 0xA8000000,
    0x51000000, 0xA3000000, 0x40000000, 0x8F000000, 0x92000000, 0x9D000000, 0x38000000, 0xF5000000,
    0xBC000000, 0xB6000000, 0xDA000000, 0x21000000, 0x10000000, 0xFF000000, 0xF3000000, 0xD2000000,
    0xCD000000, 0x0C000000, 0x13000000, 0xEC000000, 0x5F000000, 0x97000000, 0x44000000, 0x17000000,
    0xC4000000, 0xA7000000, 0x7E000000, 0x3D000000, 0x64000000, 0x5D000000, 0x19000000, 0x73000000,
    0x60000000, 0x81000000, 0x4F000000, 0xDC000000, 0x22000000, 0x2A000000, 0x90000000, 0x88000000,
    0x46000000, 0xEE000000, 0xB8000000, 0x14000000, 0xDE000000, 0x5E000000, 0x0B000000, 0xDB000000,
    0xE0000000, 0x32000000, 0x3A000000, 0x0A000000, 0x49000000, 0x06000000, 0x24000000, 0x5C000000,
    0xC2000000, 0xD3000000, 0xAC000000, 0x62000000, 0x91000000, 0x95000000, 0xE4000000, 0x79000000,
    0xE7000000, 0xC8000000, 0x37000000, 0x6D000000, 0x8D000000, 0xD5000000, 0x4E000000, 0xA9000000,
    0x6C000000, 0x56000000, 0xF4000000, 0xEA000000, 0x65000000, 0x7A000000, 0xAE000000, 0x08000000,
    0xBA000000, 0x78000000, 0x25000000, 0x2E000000, 0x1C000000, 0xA6000000, 0xB4000000, 0xC6000000,
    0xE8000000, 0xDD000000, 0x74000000, 0x1F000000, 0x4B000000, 0xBD000000, 0x8B000000, 0x8A000000,
    0x70000000, 0x3E000000, 0xB5000000, 0x66000000, 0x48000000, 0x03000000, 0xF6000000, 0x0E000000,
    0x61000000, 0x35000000, 0x57000000, 0xB9000000, 0x86000000, 0xC1000000, 0x1D000000, 0x9E000000,
    0xE1000000, 0xF8000000, 0x98000000, 0x11000000, 0x69000000, 0xD9000000, 0x8E000000, 0x94000000,
    0x9B000000, 0x1E000000, 0x87000000, 0xE9000000, 0xCE000000, 0x55000000, 0x28000000, 0xDF000000,
    0x8C000000, 0xA1000000, 0x89000000, 0x0D000000, 0xBF000000, 0xE6000000, 0x42000000, 0x68000000,
    0x41000000, 0x99000000, 0x2D000000, 0x0F000000, 0xB0000000, 0x54000000, 0xBB000000, 0x16000000
};//针对 SubWord 操作（字节替换） 的预计算表

// 1. 预定义ShiftRows的字节索引映射（关键优化）
// 原始索引 → 移位后索引（按AES规范：行0不变，行1左移1，行2左移2，行3左移3）
__constant int shift_rows_map[16] = {
    // 新位置0←原0, 1←原5, 2←原10, 3←原15
    0, 5, 10, 15,
    // 新位置4←原4, 5←原9, 6←原14, 7←原3
    4, 9, 14, 3,
    // 新位置8←原8, 9←原13, 10←原2, 11←原7
    8, 13, 2, 7,
    // 新位置12←原12, 13←原1, 14←原6, 15←原11
    12, 1, 6, 11
};



// AES加密核心函数（使用T表优化）
__kernel void aes_encrypt(
    __global const uchar* plaintext,    // 第1个参数：明文缓冲区
    __global uchar* ciphertext,         // 第2个参数：密文缓冲区
    __global const uchar* nonce,        // 第3个参数：随机数缓冲区
    __global const uchar* key,          // 第4个参数：密钥缓冲区
    ulong data_size,                    // 第5个参数：数据大小
    ulong block_count
    ){
        int N_ROUNDS_1=N_ROUNDS+1;//可能随}消蚀 
        unsigned int words[4*(N_ROUNDS+1)];
    
    // 初始化原始密钥
    int lid = get_local_id(0);
    int ls = get_local_size(0);
        #pragma unroll
        //注意：编译成pyc后可能有三个循环无法展开，原因未知。
        for (int i = get_local_id(0); i < 8; i += get_local_size(0)) {
        words[i] = (key[i*4] << 24) | (key[i*4+1] << 16) | 
                   (key[i*4+2] << 8) | key[i*4+3];
    }
    #pragma unroll
    for (int i = 0; i < 8; i++) {
            words[i] = (key[i*4] << 24) | (key[i*4+1] << 16) | 
                    (key[i*4+2] << 8) | key[i*4+3];
        }

        // 2. 三分法流水线并行 + 三元运算符优化
        #pragma unroll 
        for (int base = 8; base < 60; base += 3) {
            // Pipeline 0 (i = base)
            uint temp0 = words[base-1];
            words[base] = words[base-8] ^ 
                ((base % 8 == 0) ? (SUBWORD(ROTWORD(temp0)) ^ rcon[base/8 - 1]) :
                (base % 8 == 4) ? SUBWORD(temp0) : temp0);

            // Pipeline 1 (i = base+1)
            if (base+1 < 60) {
                uint temp1 = words[base];
                words[base+1] = words[base-7] ^ 
                    (((base+1) % 8 == 0) ? (SUBWORD(ROTWORD(temp1)) ^ rcon[(base+1)/8 - 1]) :
                    ((base+1) % 8 == 4) ? SUBWORD(temp1) : temp1);
            }

            // Pipeline 2 (i = base+2)
            if (base+2 < 60) {
                uint temp2 = words[base+1];
                words[base+2] = words[base-6] ^ 
                    (((base+2) % 8 == 0) ? (SUBWORD(ROTWORD(temp2)) ^ rcon[(base+2)/8 - 1]) :
                    ((base+2) % 8 == 4) ? SUBWORD(temp2) : temp2);
            }
        }
    

    // 扩展密钥
    int start_idx = lid * (4*(N_ROUNDS_1+ ls - 1) / ls);
    int end_idx = (lid+1) * (4*(N_ROUNDS_1) / ls);
    #pragma unroll
    for (int i = start_idx; i < end_idx; i++) {
        unsigned int temp = words[i-1];
        temp = (i % 8 == 0) ? 
        // i是8的倍数：RotWord + SubWord + Rcon
        (
            // 查表获取 RotWord 后的 SubWord 结果
            (T4_uint4[((temp << 8) | (temp >> 24)) & 0xFF].x & 0xFF000000) |
            ((T4_uint4[((temp << 8) | (temp >> 24)) & 0xFF].x & 0x00FF0000) << 8) |
            ((T4_uint4[((temp << 8) | (temp >> 24)) & 0xFF].x & 0x0000FF00) << 16) |
            ((T4_uint4[((temp << 8) | (temp >> 24)) & 0xFF].x & 0x000000FF) << 24)
        ) ^ rcon[(i/8-1) % 14] :
        (i % 8 == 4) ? 
        // i是4的倍数：仅SubWord
        (T4_uint4[(temp >> 24) & 0xFF].x & 0xFF000000) | 
        (T4_uint4[(temp >> 16) & 0xFF].x & 0x00FF0000) | 
        (T4_uint4[(temp >> 8) & 0xFF].x & 0x0000FF00) | 
        (T4_uint4[temp & 0xFF].x & 0x000000FF) :
        // 其他情况：不变换
        temp; 
        words[i] = words[i-8] ^ temp;
    }
    //最先我们用的是另外两种方法：
    //设工作组数目为n，word数组长度为m
    //第一种：工作组1处理words[1],words[n+1],words[2n+1]...
                //2处理words[2],words[n+2],words[2n+2]...
                //......
    //第二种：工作组1处理words[1],words[2],...,words[m//n]...
                //2处理words[m//n+1],words[m//n+2],...,words[2*(m//n)]...
                //......(可能不严谨，大概是这个意思。)
    //然后我们遇到了竞态条件。同一个代码有时候成功有时候失败，每次输出不一样。
    //我们构造了一个加密后立即解密的函数调用（CTR模式就是调用两次加密函数）
    //第一种写法约每16次（众数）失败才有一次成功还原原文，多的达到32次。
    //若把nonce固定，成功率会高很多，每三五次就有一次成功。
    //第二种写法在输入内容较短时没有问题，达到一定长度后成功率显著下降
    //（远远低于1/16）。问题的原因在于 words[i] = words[i-8]；words[i-8]
    //如果是其他工作组处理，可能已经处理，也可能未处理，从而导致问题。
    //最后我们只好让每个工作组都单独运算一遍数组。我觉得这里还有优化空间。
    //值得指出的是，上述问题仅在英伟达（4060）显卡运行时出现；在AMD（radeonTM890M)
    //中运行从未出现过这些问题。这反映了两者底层的一些差异。
    //这并不是一个BUG，因为并行本质上就是这样，A卡可能有其他的同步机制。
    //此外，当我试图将一些私有变量声明为本地内存存放时，A卡会报错，
    //包括同学的不同型号的A卡也会，但是N卡没有报错。
    //虽然A卡没有出现竞态条件，但是作为集成显卡它在运算速度方面还是比N卡慢一个数量级的。
    //比如N卡处理0.006s（众数）的情况A卡要0.02s这样。
    
    //主加密：   
    
    int idx = get_global_id(0);
    if (idx >= block_count) return;

    // 计算当前块的计数器值
    uchar16 nonce_uchar = vload16(0,nonce);
    uint4 nonce_vec = (uint4)(
        (nonce_uchar.s0 << 24) | (nonce_uchar.s1 << 16) | (nonce_uchar.s2 << 8) | nonce_uchar.s3,
        (nonce_uchar.s4 << 24) | (nonce_uchar.s5 << 16) | (nonce_uchar.s6 << 8) | nonce_uchar.s7,
        (nonce_uchar.s8 << 24) | (nonce_uchar.s9 << 16) | (nonce_uchar.sA << 8) | nonce_uchar.sB,
        (nonce_uchar.sC << 24) | (nonce_uchar.sD << 16) | (nonce_uchar.sE << 8) | nonce_uchar.sF
    );

    // 正确生成 increment：将 idx 按位拆分到各分量
    // 正确CTR模式：nonce（前64位） + 计数器（后64位）
    //uint4 increment = (uint4)(    //一次加密大于68GB可用
        //nonce_vec.x,               // nonce第一部分（32位）
        //nonce_vec.y,               // nonce第二部分（32位）
       // (idx >> 32) & 0xFFFFFFFF,  // 计数器高32位
       // idx & 0xFFFFFFFF           // 计数器低32位
    //);
    uint4 increment = (uint4)(//较常用
        nonce_vec.x,      // nonce的第1个32位字
        nonce_vec.y,      // nonce的第2个32位字
        nonce_vec.z,      // nonce的第3个32位字（共96位）
        idx               // 计数器（仅32位）
    );
    // 向量化计算计数器值（nonce + idx）
    ulong2 counter_128 = (ulong2)(
        ((ulong)increment.y << 32) | increment.x,  // 低64位
        ((ulong)increment.w << 32) | increment.z   // 高64位
    );
    //如果处理小数据，可以不用ulong，当时分块总是报错改的。
    //但最终每块还是分得很小，具体见下文。

    // 转换回uint4
    uint4 counter = (uint4)(counter_128.lo & 0xFFFFFFFF, 
                    (counter_128.lo >> 32) & 0xFFFFFFFF,
                    counter_128.hi & 0xFFFFFFFF, 
                    (counter_128.hi >> 32) & 0xFFFFFFFF);

    uint4 state_vec= counter;

    // 初始轮密钥加法
    state_vec^= vload4(0, &words[0]);

    // 主轮加密（使用T表）
    // 使用向量类型和操作进行向量化
    // 初始加载状态

    AES_ROUND(state_vec, 0); 
    AES_ROUND(state_vec, 1); 
    AES_ROUND(state_vec, 2); 
    AES_ROUND(state_vec, 3); 
    AES_ROUND(state_vec, 4); 
    AES_ROUND(state_vec, 5); 
    AES_ROUND(state_vec, 6); 
    AES_ROUND(state_vec, 7); 
    AES_ROUND(state_vec, 8); 
    AES_ROUND(state_vec, 9); 
    AES_ROUND(state_vec, 10); 
    AES_ROUND(state_vec, 11); 
    AES_ROUND(state_vec, 12); 
    AES_ROUND(state_vec, 13); 
     
    // 最后一轮（不用MixColumns，使用普通的SubBytes+ShiftRows）
    uchar16 state_bytes = as_uchar16(state_vec);
        uchar16 result_bytes;
        #pragma unroll
        for (int i = 0; i < 16; i++) {
            uchar sbox_val = (Te4[state_bytes[i]] >> 24) & 0xFF;
            result_bytes[shift_rows_map[i]] = sbox_val;
        }
        state_vec = as_uint4(result_bytes);

    // 以上用的是查表法，文献中还有一个比特滑动窗口的方法，适合小内存场景使用，
    //实现较复杂，要注意边界。发现与查表是作用于同一位点的，有查表就不用滑动窗口了。

    //  AddRoundKey：轮密钥异或
    uint4 final_state;
    final_state.x = state_vec.x ^ words[N_ROUNDS*4 + 0];
    final_state.y = state_vec.y ^ words[N_ROUNDS*4 + 1];
    final_state.z = state_vec.z ^ words[N_ROUNDS*4 + 2];
    final_state.w = state_vec.w ^ words[N_ROUNDS*4 + 3];
    
    // 生成密钥流（使用向量操作）
    // 更高效的实现（假设支持向量类型转换）
    uchar16 keystream = (uchar16)(
        (uchar4)(final_state.x), (uchar4)(final_state.y),
        (uchar4)(final_state.z), (uchar4)(final_state.w)
    );
    
    // 明文与密钥流异或得到密文
    uint offset = idx * BLOCK_SIZE;
    uint remaining = data_size - offset;
    #pragma unroll
    for (int i = 0; i < min((uint)BLOCK_SIZE, remaining); i++) {
                ciphertext[offset + i] = plaintext[offset + i] ^ keystream[i];
    }   
}
"""

class AESOpenCL:
    def __init__(self):
        # 选择第一个可用的平台和设备
        platforms = cl.get_platforms()
        platform = platforms[0]  # 默认选择第一个平台
        devices = platform.get_devices(device_type=cl.device_type.GPU)
        
        # 如果没有GPU，尝试使用CPU
        if not devices:
            devices = platform.get_devices(device_type=cl.device_type.CPU)
            print("未找到GPU设备，将使用CPU进行计算")
        
        self.ctx = cl.Context(devices=devices)
        self.queue = cl.CommandQueue(self.ctx)
        self.program = cl.Program(self.ctx, opencl_kernel).build() 
        self.device = self.ctx.devices[0] 
        self.key_buf = None
    def encrypt(self, data, key,m,encoding='utf-8'):
        """支持分块处理的大数据加密方法"""
        # 转换输入数据为bytes
        if isinstance(data, str):
            data = data.encode(encoding)
        
        # 检查密钥长度
        if len(key) != 32:
            raise ValueError("AES-256密钥必须是32字节长")
        
        # 确保密钥缓冲区已初始化
        if self.key_buf is None:
            key_np = np.frombuffer(key, dtype=np.uint8)
            mf = cl.mem_flags
            self.key_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=key_np)
        if m=='e':
            # 生成nonce（整个加密过程使用同一个）
            random_part = os.urandom(8)
            timestamp_part = int(time.time()).to_bytes(8, 'big')
            nonce = random_part + timestamp_part
        else:
            nonce=data[:16]
            data=data[16:]
        # 初始化输出缓冲区
        ciphertext = bytearray()
        total_size = len(data)
        
        # 保守的分块大小计算
        max_alloc = self.device.get_info(cl.device_info.MAX_MEM_ALLOC_SIZE)
        # 确保有足够的内存余量
        chunk_size = int(max_alloc * 0.8)  # pyright: ignore[reportOperatorIssue] #这个可以按照实际调整。
        #我不知道为什么这个会远远小于硬件显存。可能cl的调用和那些电子游戏的调用不一样。
        chunk_size = (chunk_size // 16) * 16  # 确保是16的倍数
        chunk_size = max(chunk_size, 16 * 1024)  # 最小16KB
        chunk_size = min(chunk_size, 1024 * 1024 * 3200)  
        # 最大3200MB，防止过大，主要是防止device有这么多但是系统不能分配给你这么多。
        #可以自行解除限制。

        print(f"使用分块大小: {chunk_size} bytes")
        
        # 分块处理
        for offset in range(0, total_size, chunk_size):
            try:
                chunk = data[offset:offset+chunk_size]
                print(f"处理块 {offset//chunk_size + 1}/{(total_size + chunk_size -1)//chunk_size}, 大小: {len(chunk)} bytes")
                
                # 加密当前块并添加到结果
                encrypted_chunk = self._encrypt_chunk(chunk, key, nonce, offset//16)
                ciphertext.extend(encrypted_chunk)
                
                # 强制同步并清理
                self.queue.finish()
            except Exception as e:
                print(f"处理块时出错: {e}")
                # 尝试更小的块大小重试
                smaller_chunk_size = max(chunk_size // 2, 64 * 1024)
                print(f"尝试使用更小的块大小: {smaller_chunk_size} bytes")
                
                # 处理当前块
                sub_offset = offset
                while sub_offset < offset + chunk_size and sub_offset < total_size:
                    sub_chunk = data[sub_offset:sub_offset+smaller_chunk_size]
                    encrypted_subchunk = self._encrypt_chunk(sub_chunk, key, nonce, sub_offset//16)
                    ciphertext.extend(encrypted_subchunk)
                    sub_offset += smaller_chunk_size
                    self.queue.finish()
        
        return nonce + bytes(ciphertext)
    '''
    由于设备所限，我们目前只能确保分块后能加密比分块前更多的数据，
    并在解密时能够复原。在进一步探索时，我们遇到了其他方面的阻碍。
    具体来说，当我们把一个25G的文件放进去后，虽然程序最终运行完成，
    但是由于内存占满，需要强制写入硬盘再处理剩余数据，中途频繁卡顿，
    这已经成为整体耗时的主要原因。9分多钟里除了开头处理较多块并且内存占用迅速上升，
    之后内存占用呈波浪式起伏。处理数据时占用迅速上升，至顶端卡住，然后系统开始
    写盘，磁盘活动明显增强，内存开始缓慢下降，降至六成左右继续处理数据，又迅速上升，
    循环多次。约4/5的时间程序是卡住的。
    考虑到对磁盘的损害，我们将停止进一步探索和优化更大的数据处理方案，尽管我们
    调用GPU和OPENCL的初心就是探索优化大数据并行处理。
    '''
    def _encrypt_chunk(self, chunk, key, nonce, counter_offset):
        """处理单个数据块的内部方法"""
        # 准备数据
        plaintext_np = np.frombuffer(chunk, dtype=np.uint8)
        data_size = len(plaintext_np)
        block_count = (data_size + 15) // 16
        
        # 创建buffer（使用更安全的内存标志）
        mf = cl.mem_flags
        try:
            plaintext_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=plaintext_np)
            ciphertext_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, data_size)
            
            # 计算带偏移的计数器
            counter = self._calculate_counter(nonce, counter_offset)
            nonce_np = np.frombuffer(counter, dtype=np.uint8)
            nonce_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=nonce_np)
            
            # 执行内核
            global_size = self._calculate_global_size(block_count)
            local_size = None  # 让OpenCL驱动自动选择最佳本地大小
            

            # q=time.time()#开始执行内核函数时间。
            self.program.aes_encrypt(
                self.queue, (global_size,), local_size,
                plaintext_buf, ciphertext_buf, nonce_buf, self.key_buf,
                np.uint(data_size), np.uint(block_count)
            )
            
            # 等待内核完成
            # self.queue.finish()#如果要统计计算用时，把它打开，如果只给用户使用，不必这一步。
            # print('用时:',time.time()-q)
            # 获取结果 - 使用分页锁定内存可能有助于性能
            result = np.empty(data_size, dtype=np.uint8)
            evt = cl.enqueue_copy(self.queue, result, ciphertext_buf)
            evt.wait()  # 等待复制完成
            '''若enqueue_copy是队列中最后一个任务，且之前的任务都已完成：两者性能几乎无差异（finish()实际也只等复制操作）。
            若队列中还有其他未完成的任务：finish()需要等待所有任务，耗时可能远大于evt.wait()（仅等复制）。'''
            
            return result.tobytes()
            
        except Exception as e:
            print(f"加密块时出错: {e}")
            raise
        finally:
            # 确保资源被释放
            try:
                plaintext_buf.release() # pyright: ignore[reportPossiblyUnboundVariable]
            except:
                pass
            try:
                ciphertext_buf.release() # pyright: ignore[reportPossiblyUnboundVariable]
            except:
                pass
            try:
                nonce_buf.release() # pyright: ignore[reportPossiblyUnboundVariable]
            except:
                pass
            # 再次确保队列完成所有操作
            self.queue.finish()

    def _calculate_global_size(self, block_count):
        """计算更安全的global_size"""
        device = self.device
        max_work_group_size = device.get_info(cl.device_info.MAX_WORK_GROUP_SIZE)
        
        # 选择一个合理的工作组大小
        group_size = min(512, max_work_group_size)  # pyright: ignore[reportArgumentType] 
        # 256是一个安全的默认值
        #似乎关系不大，设为2048，128，16加密相同的 1528008539 bytes数据，耗时 0.2346806526184082秒，
        #0.23544096946716309秒，和0.2385103702545166秒，关键耗时还是分块和多次调用内核那里。
   
        # 计算全局大小，确保是工作组大小的倍数
        global_size = ((block_count + group_size - 1) // group_size) * group_size
        
        # 设置上限，防止资源耗尽
        max_possible_global_size = max_work_group_size * 2048 # pyright: ignore[reportOperatorIssue]
        #这个可以自行调整，网上说1024是经验值，但现代GPU能力已经超过1024，再用会增加闲置计算单元。
        return min(global_size, max_possible_global_size)  

    def _calculate_counter(self, nonce, offset):
        """128位安全计数器递增"""
        nonce_int = int.from_bytes(nonce, 'big')
        counter = nonce_int + offset
        return counter.to_bytes(16, 'big')


# 示例用法
def begin(ip,key,m=None):
    if m=='e':
        print('为确保安全，请及时备份源文件。')
        aes = AESOpenCL()
        key = key.encode('utf-32')#七个字符（含标点），如‘左牵黄，右擎苍’，表情不可以
        with open(ip,'rb')as f:
            plaintext_bytes =f.read()  
        # 加密
        encrypted_data = aes.encrypt(plaintext_bytes, key,m)
        print(f"Nonce: {encrypted_data[:16].hex()}")
        # print(f"原文: {bytes.fromhex(encrypted_data[16:].hex()).decode(encoding='utf-8')}") 
        with open(ip+'已加密'+os.path.splitext(ip)[1],'wb')as f:
            f.write(encrypted_data)
        print('输出提示中，Nonce确保相同原文和密钥在每次加密时密文不重复；"overriding noinline attribute"说明编译器正在忽略noinline设置，与编译器内部设置有关；内核多次调用是分块处理所必需，循环无法展开是预编译与源代码之间有略微差异，无需在意。')
        print('finish\n为确保安全，请自行决定是否删除源文件。')
    else:
        aes = AESOpenCL()
        key = key.encode('utf-32')#七个字符（含标点），如‘左牵黄，右擎苍’，表情不可以
        with open(ip,'rb')as f:
            plaintext_bytes =f.read()  
        encrypted_data = aes.encrypt(plaintext_bytes, key,m)
        # print(f"原文: {bytes.fromhex(encrypted_data[16:].hex()).decode(encoding='utf-8')}") 
        with open(ip+'已解密'+os.path.splitext(ip)[1],'wb')as f:
            f.write(encrypted_data[16:])
        print('finish')
# begin(r'core\recognise\medium.pt','左牵黄，右擎苍','e')
