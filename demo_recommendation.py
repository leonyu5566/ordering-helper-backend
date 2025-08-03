#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推薦店家功能演示
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_recommendation_system():
    """演示推薦系統功能"""
    print("🍽️ 推薦店家功能演示")
    print("=" * 50)
    
    # 模擬使用者需求
    user_requests = [
        {
            "user": "小明",
            "language": "zh",
            "request": "我想要吃辣的食物",
            "description": "小明想要吃辣味料理"
        },
        {
            "user": "Sarah",
            "language": "en", 
            "request": "I'm looking for Italian cuisine",
            "description": "Sarah 在找義大利料理"
        },
        {
            "user": "田中さん",
            "language": "ja",
            "request": "ベジタリアンオプションが必要です",
            "description": "田中さん需要素食選項"
        },
        {
            "user": "김민수",
            "language": "ko",
            "request": "디저트를 먹고 싶어요",
            "description": "김민수想要吃甜點"
        }
    ]
    
    print(f"📋 共有 {len(user_requests)} 個使用者需求")
    
    for i, user_req in enumerate(user_requests, 1):
        print(f"\n👤 使用者 {i}: {user_req['user']} ({user_req['language']})")
        print(f"   需求: {user_req['request']}")
        print(f"   描述: {user_req['description']}")
        
        # 模擬 AI 推薦過程
        print("   🤖 AI 分析中...")
        
        # 模擬推薦結果
        recommendations = simulate_ai_recommendations(user_req['request'])
        
        if recommendations:
            print(f"   ✅ 找到 {len(recommendations)} 個推薦:")
            for j, rec in enumerate(recommendations, 1):
                partner_level_text = {0: "非合作", 1: "合作", 2: "VIP"}[rec['partner_level']]
                print(f"      {j}. {rec['store_name']} ({partner_level_text})")
                print(f"         理由: {rec['reason']}")
                print(f"         評分: {rec['estimated_rating']}")
        else:
            print("   ❌ 沒有找到合適的推薦")
        
        print("   " + "-" * 40)
    
    print("\n🎯 推薦系統特色:")
    print("   ✅ 智能需求分析")
    print("   ✅ 多語言支援")
    print("   ✅ AI 驅動推薦")
    print("   ✅ 優先級排序 (VIP > 合作 > 非合作)")
    print("   ✅ 個性化推薦理由")

def simulate_ai_recommendations(food_request):
    """模擬 AI 推薦結果"""
    # 模擬的店家資料庫
    mock_stores = [
        {
            "store_id": 1,
            "store_name": "川味小館",
            "partner_level": 2,  # VIP
            "reason": "提供正宗川菜，辣味十足，符合您的需求",
            "matched_keywords": ["辣", "川菜", "spicy", "hot"],
            "estimated_rating": "4.5星"
        },
        {
            "store_id": 2,
            "store_name": "義大利麵工坊",
            "partner_level": 1,  # 合作
            "reason": "提供道地義大利料理，包括各種義大利麵和披薩",
            "matched_keywords": ["義大利", "Italian", "pasta", "pizza"],
            "estimated_rating": "4.2星"
        },
        {
            "store_id": 3,
            "store_name": "素食天地",
            "partner_level": 1,  # 合作
            "reason": "專門提供健康美味的素食料理",
            "matched_keywords": ["素食", "vegetarian", "vegan", "ベジタリアン"],
            "estimated_rating": "4.0星"
        },
        {
            "store_id": 4,
            "store_name": "壽司大師",
            "partner_level": 0,  # 非合作
            "reason": "新鮮的日式壽司和刺身",
            "matched_keywords": ["日本", "Japanese", "壽司", "sushi"],
            "estimated_rating": "4.3星"
        },
        {
            "store_id": 5,
            "store_name": "甜點工坊",
            "partner_level": 0,  # 非合作
            "reason": "精緻的手工甜點和蛋糕",
            "matched_keywords": ["甜點", "dessert", "蛋糕", "cake", "디저트"],
            "estimated_rating": "4.1星"
        },
        {
            "store_id": 6,
            "store_name": "火鍋王",
            "partner_level": 2,  # VIP
            "reason": "提供多種湯底的火鍋，辣味湯底特別受歡迎",
            "matched_keywords": ["火鍋", "辣", "hot pot", "spicy"],
            "estimated_rating": "4.6星"
        },
        {
            "store_id": 7,
            "store_name": "披薩專賣店",
            "partner_level": 1,  # 合作
            "reason": "正宗義大利披薩，多種口味選擇",
            "matched_keywords": ["披薩", "pizza", "義大利", "Italian"],
            "estimated_rating": "4.3星"
        }
    ]
    
    # 根據需求關鍵字篩選
    filtered_stores = []
    for store in mock_stores:
        if any(keyword.lower() in food_request.lower() for keyword in store['matched_keywords']):
            filtered_stores.append(store)
    
    # 按照合作等級排序
    filtered_stores.sort(key=lambda x: x['partner_level'], reverse=True)
    
    return filtered_stores[:3]  # 返回前3個推薦

def demo_line_bot_integration():
    """演示 LINE Bot 整合"""
    print("\n🤖 LINE Bot 整合演示")
    print("=" * 50)
    
    # 模擬 LINE Bot 對話流程
    conversation_flow = [
        {
            "user": "我想要吃辣的食物",
            "bot_response": "🍽️ 根據您的需求，我為您推薦以下店家：\n\n1. **川味小館** (VIP)\n   📝 提供正宗川菜，辣味十足，符合您的需求\n   ⭐ 4.5星\n\n2. **火鍋王** (VIP)\n   📝 提供多種湯底的火鍋，辣味湯底特別受歡迎\n   ⭐ 4.6星\n\n💡 您可以分享位置來查看這些店家的詳細資訊和開始點餐。"
        },
        {
            "user": "I'm looking for Italian cuisine",
            "bot_response": "🍽️ Based on your request, I recommend the following restaurants:\n\n1. **義大利麵工坊** (Partner)\n   📝 提供道地義大利料理，包括各種義大利麵和披薩\n   ⭐ 4.2星\n\n2. **披薩專賣店** (Partner)\n   📝 正宗義大利披薩，多種口味選擇\n   ⭐ 4.3星\n\n💡 You can share your location to view detailed information and start ordering from these restaurants."
        }
    ]
    
    for i, flow in enumerate(conversation_flow, 1):
        print(f"\n💬 對話 {i}:")
        print(f"   使用者: {flow['user']}")
        print(f"   Bot: {flow['bot_response']}")
        print("   " + "-" * 40)

def demo_technical_features():
    """演示技術特色"""
    print("\n⚙️ 技術特色演示")
    print("=" * 50)
    
    features = [
        {
            "feature": "智能需求識別",
            "description": "自動識別餐飲相關關鍵字",
            "keywords": ["想吃", "想要", "推薦", "找", "餐廳", "美食", "料理", "菜", "飯", "麵", "火鍋", "燒烤", "壽司", "披薩", "漢堡", "咖啡", "飲料", "甜點"]
        },
        {
            "feature": "多語言支援",
            "description": "支援中文、英文、日文、韓文",
            "languages": ["中文 (zh)", "English (en)", "日本語 (ja)", "한국어 (ko)"]
        },
        {
            "feature": "AI 驅動推薦",
            "description": "使用 Gemini API 進行智能分析",
            "capabilities": ["需求分析", "店家匹配", "個性化推薦", "理由生成"]
        },
        {
            "feature": "優先級排序",
            "description": "按照合作等級排序推薦結果",
            "priority": ["VIP 店家 (最高)", "合作店家 (中等)", "非合作店家 (最低)"]
        }
    ]
    
    for feature in features:
        print(f"\n🔧 {feature['feature']}")
        print(f"   描述: {feature['description']}")
        if 'keywords' in feature:
            print(f"   關鍵字: {', '.join(feature['keywords'][:5])}...")
        elif 'languages' in feature:
            print(f"   支援語言: {', '.join(feature['languages'])}")
        elif 'capabilities' in feature:
            print(f"   功能: {', '.join(feature['capabilities'])}")
        elif 'priority' in feature:
            print(f"   優先級: {' > '.join(feature['priority'])}")

def main():
    """主演示函數"""
    print("🚀 推薦店家功能完整演示")
    print("=" * 60)
    
    # 1. 推薦系統演示
    demo_recommendation_system()
    
    # 2. LINE Bot 整合演示
    demo_line_bot_integration()
    
    # 3. 技術特色演示
    demo_technical_features()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("\n📝 功能總結:")
    print("   ✅ 使用者提出餐飲需求")
    print("   ✅ 系統調用 Gemini API 分析需求")
    print("   ✅ 按照 VIP > 合作 > 非合作 排序")
    print("   ✅ 提供個性化推薦理由")
    print("   ✅ 支援多語言介面")
    print("\n🔧 部署需求:")
    print("   - 設定 GEMINI_API_KEY 環境變數")
    print("   - 設定 LINE Bot 環境變數")
    print("   - 確保資料庫中有店家資料")
    print("   - 部署到支援 HTTPS 的伺服器")

if __name__ == "__main__":
    main() 