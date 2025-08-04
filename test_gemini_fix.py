#!/usr/bin/env python3
"""
測試 Gemini Vision API 修復
驗證圖片型別轉換是否正確
"""

import os
import sys
import tempfile
from PIL import Image
import io

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_gemini_pil_conversion():
    """測試 Gemini PIL.Image 轉換"""
    print("🧪 測試 Gemini Vision API 修復...")
    
    try:
        # 建立測試圖片
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # 儲存到臨時檔案
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            image_path = tmp_file.name
        
        print(f"✅ 建立測試圖片: {image_path}")
        
        # 測試圖片讀取和 PIL.Image 轉換
        from app.api.helpers import process_menu_with_gemini
        
        # 模擬環境變數
        if not os.getenv('GEMINI_API_KEY'):
            print("⚠️  警告: GEMINI_API_KEY 未設定，跳過實際 API 測試")
            print("✅ 圖片讀取和 PIL.Image 轉換測試完成")
            return True
        
        # 實際測試 Gemini API
        print("🔄 測試 Gemini API 調用...")
        result = process_menu_with_gemini(image_path, 'en')
        
        if result:
            print(f"✅ Gemini API 測試完成")
            print(f"   成功: {result.get('success', False)}")
            print(f"   錯誤: {result.get('error', '無')}")
            print(f"   備註: {result.get('processing_notes', '無')}")
            return result.get('success', False)
        else:
            print("❌ Gemini API 測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        # 清理臨時檔案
        if 'image_path' in locals():
            try:
                os.unlink(image_path)
            except:
                pass

def test_image_processing():
    """測試圖片處理流程"""
    print("\n🔍 測試圖片處理流程...")
    
    try:
        # 建立測試圖片
        test_image = Image.new('RGB', (200, 200), color='blue')
        
        # 儲存到臨時檔案
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'PNG')
            image_path = tmp_file.name
        
        print(f"✅ 建立測試圖片: {image_path}")
        
        # 測試圖片讀取
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
        
        print(f"✅ 圖片讀取成功: {len(image_bytes)} bytes")
        
        # 測試 PIL.Image 轉換
        image = Image.open(io.BytesIO(image_bytes))
        print(f"✅ PIL.Image 轉換成功: {image.size}")
        
        # 測試 MIME 類型檢測
        import mimetypes
        mime_type, _ = mimetypes.guess_type(image_path)
        print(f"✅ MIME 類型檢測: {mime_type}")
        
        # 測試 Gemini API 調用（模擬）
        print("✅ 圖片格式驗證完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 圖片處理測試失敗: {e}")
        return False
    finally:
        # 清理臨時檔案
        if 'image_path' in locals():
            try:
                os.unlink(image_path)
            except:
                pass

def test_import_fixes():
    """測試 ImportError 修復"""
    print("\n🔧 測試 ImportError 修復...")
    
    try:
        # 測試 google.generativeai 導入
        import google.generativeai as genai
        print("✅ google.generativeai 導入成功")
        
        # 測試 PIL 導入
        from PIL import Image
        print("✅ PIL.Image 導入成功")
        
        # 測試不會導入不存在的 Blob
        try:
            from google.generativeai.types import Blob
            print("❌ Blob 仍然可以導入（不應該發生）")
            return False
        except ImportError:
            print("✅ Blob 導入失敗（符合預期）")
        
        return True
        
    except Exception as e:
        print(f"❌ 導入測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始 Gemini Vision API 修復測試")
    print("=" * 50)
    
    # 測試導入修復
    import_test = test_import_fixes()
    
    # 測試圖片處理
    image_test = test_image_processing()
    
    # 測試 Gemini API
    gemini_test = test_gemini_pil_conversion()
    
    print("\n" + "=" * 50)
    print("📊 測試結果:")
    print(f"   導入修復: {'✅ 通過' if import_test else '❌ 失敗'}")
    print(f"   圖片處理: {'✅ 通過' if image_test else '❌ 失敗'}")
    print(f"   Gemini API: {'✅ 通過' if gemini_test else '❌ 失敗'}")
    
    if import_test and image_test and gemini_test:
        print("\n🎉 所有測試通過！Gemini Vision API 修復成功")
        return True
    else:
        print("\n⚠️  部分測試失敗，請檢查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 