#!/usr/bin/env python3
"""
调试主题提取逻辑
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService

def debug_topic_extraction():
    """调试主题提取逻辑"""
    print("=== 调试主题提取逻辑 ===\n")
    
    service = AIChatService()
    
    # 测试消息
    messages = [
        "I'm struggling with data structures",
        "I find sorting algorithms difficult",
        "I'm weak in Python loops and functions"
    ]
    
    for message in messages:
        print(f"消息: '{message}'")
        
        # 提取主题
        topic = service.extract_weak_topic(message)
        print(f"提取的主题: '{topic}'")
        
        if topic:
            # 检查主题是否具体
            is_specific = service.is_topic_specific(topic)
            print(f"主题是否具体: {is_specific}")
            
            # 检查技术关键词
            technical_keywords = [
                'data', 'algorithm', 'program', 'python', 'java', 'javascript', 'loop', 'function', 
                'variable', 'array', 'list', 'dictionary', 'recursion', 'sort', 'search', 'class', 
                'object', 'inheritance', 'database', 'sql', 'web', 'html', 'css', 'react', 'vue', 
                'angular', 'node', 'express', 'django', 'flask', 'machine', 'learning', 'ai', 
                'neural', 'network', 'deep', 'statistic', 'probability', 'math', 'calculus', 
                'computer', 'software', 'complexity', 'dynamic', 'greedy', 'divide', 'conquer', 
                'backtrack', 'graph', 'tree', 'linked', 'stack', 'queue', 'hash', 'binary', 
                'heap', 'priority', 'bubble', 'quick', 'merge', 'insertion', 'selection', 
                'counting', 'radix', 'bucket'
            ]
            
            has_technical_keyword = any(keyword in topic.lower() for keyword in technical_keywords)
            print(f"包含技术关键词: {has_technical_keyword}")
            
            # 检查模糊词汇
            vague_terms = ['everything', 'anything', 'something', 'stuff', 'things', 'all', 'general']
            is_vague = any(term in topic.lower() for term in vague_terms)
            print(f"包含模糊词汇: {is_vague}")
            
            print(f"最终判断: {'具体' if has_technical_keyword and not is_vague else '模糊'}")
        
        print("-" * 60)

if __name__ == "__main__":
    debug_topic_extraction()