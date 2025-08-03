#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除裝飾器
"""

import re

def remove_decorators():
    """移除裝飾器"""
    
    # 讀取檔案
    with open('app/webhook/routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除裝飾器
    content = re.sub(
        r'@get_line_bot_handler\(\)\.add\([^)]+\)\n',
        '',
        content
    )
    
    # 寫回檔案
    with open('app/webhook/routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 裝飾器移除完成")

if __name__ == "__main__":
    remove_decorators() 