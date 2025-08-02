# =============================================================================
# 檔案名稱：app/webhook/routes.py
# 功能描述：處理 LINE Bot 的 Webhook 請求，實現 LINE Bot 的核心功能
# 主要職責：
# - 處理 LINE 平台發送的訊息事件
# - 管理使用者語言設定
# - 處理店家查詢請求
# - 處理訂單記錄查詢
# - 發送語音訂單訊息
# 支援功能：
# - 多語言歡迎訊息
# - 位置分享處理
# - 訂單狀態查詢
# - 語音訊息推送
# =============================================================================

from flask import request, abort, Blueprint, jsonify
from ..models import db, User, Store, Order, VoiceFile
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    ImageMessage, LocationMessage, FlexSendMessage,
    AudioSendMessage, QuickReply, QuickReplyButton,
    MessageAction
)

webhook_bp = Blueprint('webhook', __name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@webhook_bp.route("/callback", methods=['POST'])
def callback():
    """LINE Bot Webhook 處理器"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    text = event.message.text
    
    # 檢查使用者是否存在
    user = User.query.filter_by(line_user_id=user_id).first()
    
    if not user:
        # 新使用者，引導選擇語言
        handle_new_user(event)
    else:
        # 現有使用者，處理一般訊息
        handle_existing_user(event, user, text)

def handle_new_user(event):
    """處理新使用者加入"""
    user_id = event.source.user_id
    
    # 建立語言選擇選單
    quick_reply = QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label="English", text="I prefer English")
            ),
            QuickReplyButton(
                action=MessageAction(label="日本語", text="日本語を選択")
            ),
            QuickReplyButton(
                action=MessageAction(label="한국어", text="한국어를 선택")
            ),
            QuickReplyButton(
                action=MessageAction(label="中文", text="我選擇中文")
            )
        ]
    )
    
    welcome_message = "歡迎使用點餐小幫手！\n請選擇您的語言偏好：\n\nWelcome to Ordering Helper!\nPlease select your language preference:"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_message, quick_reply=quick_reply)
    )

def handle_existing_user(event, user, text):
    """處理現有使用者的訊息"""
    user_id = event.source.user_id
    
    if text in ["I prefer English", "日本語を選択", "한국어를 선택", "我選擇中文"]:
        # 處理語言選擇
        lang_map = {
            "I prefer English": "en",
            "日本語を選択": "ja", 
            "한국어를 선택": "ko",
            "我選擇中文": "zh"
        }
        
        user.preferred_lang = lang_map[text]
        db.session.commit()
        
        # 發送歡迎訊息
        welcome_messages = {
            "en": "Welcome! I'm your ordering assistant. I can help you find restaurants and order food in Chinese.",
            "ja": "ようこそ！注文アシスタントです。中国語でレストランを見つけて注文するお手伝いをします。",
            "ko": "환영합니다! 주문 도우미입니다. 중국어로 레스토랑을 찾고 음식을 주문하는 것을 도와드릴 수 있습니다.",
            "zh": "歡迎！我是您的點餐小幫手。我可以幫您找到餐廳並用中文點餐。"
        }
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=welcome_messages[user.preferred_lang])
        )
    
    elif text.lower() in ["find restaurants", "レストランを探す", "레스토랑 찾기", "找餐廳"]:
        # 處理找餐廳請求
        handle_find_restaurants(event, user)
    
    elif text.lower() in ["order history", "注文履歴", "주문 내역", "訂單記錄"]:
        # 處理查詢訂單記錄
        handle_order_history(event, user)
    
    else:
        # 一般對話處理
        handle_general_conversation(event, user, text)

def handle_find_restaurants(event, user):
    """處理找餐廳請求"""
    # 這裡應該根據使用者的位置來查詢餐廳
    # 暫時回傳固定訊息
    message = "請分享您的位置，我將為您找到附近的餐廳。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

def handle_order_history(event, user):
    """處理查詢訂單記錄"""
    # 查詢使用者的訂單記錄
    orders = Order.query.filter_by(user_id=user.user_id).order_by(Order.order_time.desc()).limit(5).all()
    
    if not orders:
        message = "您還沒有訂單記錄。"
    else:
        message = "您的最近訂單：\n"
        for order in orders:
            store = Store.query.get(order.store_id)
            message += f"- {store.store_name}: ${order.total_amount}\n"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

def handle_general_conversation(event, user, text):
    """處理一般對話"""
    # 這裡可以加入 AI 對話功能
    response = "我理解您的訊息，但我目前主要專注於點餐服務。請告訴我您想要找餐廳還是查看訂單記錄。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    """處理位置訊息"""
    user_id = event.source.user_id
    user = User.query.filter_by(line_user_id=user_id).first()
    
    if not user:
        return
    
    # 取得位置資訊
    latitude = event.message.latitude
    longitude = event.message.longitude
    
    # TODO: 根據位置查詢附近餐廳
    # 這裡應該呼叫 API 來取得附近餐廳資訊
    
    message = f"收到您的位置！正在為您尋找附近的餐廳..."
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

def send_voice_order(order_id):
    """發送語音訂單到 LINE"""
    """這個函數會在訂單建立後被呼叫"""
    order = Order.query.get(order_id)
    if not order:
        return
    
    user = User.query.get(order.user_id)
    if not user:
        return
    
    # TODO: 生成語音檔案
    # 1. 將訂單轉換為中文文字
    # 2. 呼叫 TTS API 生成語音
    # 3. 儲存語音檔案
    # 4. 發送到 LINE
    
    # 暫時發送文字訊息
    message = f"您的訂單已確認！\n訂單編號：{order.order_id}\n總金額：${order.total_amount}"
    
    try:
        line_bot_api.push_message(
            user.line_user_id,
            TextSendMessage(text=message)
        )
    except Exception as e:
        print(f"發送訊息失敗：{e}")
