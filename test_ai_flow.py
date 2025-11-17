#!/usr/bin/env python3
"""
测试AI模块数据流的独立脚本
用于验证：前端 → 后端 → AI模块 → Gemini → 调度器 → 前端 的完整流程
"""

import os
import sys
import django
from pathlib import Path

# 添加Django项目路径
project_root = Path(__file__).parent / "django_backend"
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

# 现在可以导入Django模块
from ai_module.plan_generator import generate_plan
from ai_module.pdf_ingest import extract_text_from_pdf

def test_pdf_extraction():
    """测试PDF文本提取"""
    print("🔍 测试PDF文本提取...")
    
    pdf_path = "/task/comp9900/9900assignment2.pdf"
    text = extract_text_from_pdf(pdf_path)
    
    if text:
        print(f"✅ PDF提取成功，文本长度: {len(text)} 字符")
        print(f"📄 前100字符预览: {text[:100]}...")
        return True
    else:
        print("❌ PDF提取失败")
        return False

def test_ai_plan_generation():
    """测试AI计划生成"""
    print("\n🤖 测试AI计划生成...")
    
    # 模拟偏好数据
    preferences = {
        "dailyHours": 4,
        "weeklyStudyDays": 5,
        "avoidDays": ["Sat", "Sun"]
    }
    
    # 模拟任务数据
    tasks_meta = []
    
    try:
        result = generate_plan(preferences, tasks_meta)
        print(f"✅ AI计划生成成功")
        print(f"📊 结果类型: {type(result)}")
        print(f"📊 结果键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            if result.get("ok"):
                print(f"✅ 计划状态: 成功")
                if "days" in result:
                    print(f"📅 生成天数: {len(result['days'])}")
                if "aiSummary" in result:
                    print(f"🧠 AI摘要: 已包含")
            else:
                print(f"⚠️ 计划状态: {result.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        print(f"❌ AI计划生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_gemini_connection():
    """测试Gemini连接"""
    print("\n🔗 测试Gemini连接...")
    
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ Gemini API密钥已配置 (长度: {len(gemini_key)})")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # 简单测试
            response = model.generate_content("Hello, respond with 'AI connection successful'")
            if response and hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].content.parts[0].text
                print(f"✅ Gemini响应: {text}")
                return True
            else:
                print("❌ Gemini响应格式异常")
                return False
                
        except Exception as e:
            print(f"❌ Gemini连接失败: {e}")
            return False
    else:
        print("❌ Gemini API密钥未配置")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试AI模块数据流...\n")
    
    # 测试1: PDF提取
    pdf_ok = test_pdf_extraction()
    
    # 测试2: Gemini连接
    gemini_ok = test_gemini_connection()
    
    # 测试3: AI计划生成
    plan_result = test_ai_plan_generation()
    
    # 总结
    print("\n📋 测试总结:")
    print(f"PDF提取: {'✅' if pdf_ok else '❌'}")
    print(f"Gemini连接: {'✅' if gemini_ok else '❌'}")
    print(f"AI计划生成: {'✅' if plan_result else '❌'}")
    
    if pdf_ok and gemini_ok and plan_result:
        print("\n🎉 所有测试通过！AI模块数据流正常。")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查相关配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)