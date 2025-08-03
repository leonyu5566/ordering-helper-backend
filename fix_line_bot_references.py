#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 LINE Bot API 引用
"""

import re

def fix_line_bot_references():
    """修復 LINE Bot API 引用"""
    
    # 讀取檔案
    with open('app/webhook/routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修復 line_bot_api 引用
    # 將 line_bot_api. 替換為 get_line_bot_api().
    content = re.sub(
        r'line_bot_api\.',
        r'get_line_bot_api().',
        content
    )
    
    # 修復 handler 引用
    # 將 handler. 替換為 get_line_bot_handler().
    content = re.sub(
        r'handler\.',
        r'get_line_bot_handler().',
        content
    )
    
    # 修復 gemini_model 引用
    # 將 gemini_model. 替換為 get_gemini_model().
    content = re.sub(
        r'gemini_model\.',
        r'get_gemini_model().',
        content
    )
    
    # 寫回檔案
    with open('app/webhook/routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ LINE Bot API 引用修復完成")

if __name__ == "__main__":
    fix_line_bot_references() 