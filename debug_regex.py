#!/usr/bin/env python3
"""
调试正则表达式
"""
import re

def debug_regex():
    """调试正则表达式"""
    print("=== 调试正则表达式 ===\n")
    
    message = "I find sorting algorithms difficult"
    
    # 测试新的正则表达式
    pattern = r'(?:find.*difficult|find.*challenging|find.*hard)\s+([a-zA-Z\s]+(?:data\s+structures|algorithms|programming|python|java|javascript|loops|functions|variables|arrays|lists|dictionaries|recursion|sorting|searching|classes|objects|inheritance|polymorphism|database|sql|web\s+development|html|css|react|vue|angular|node\.js|express|django|flask|machine\s+learning|artificial\s+intelligence|neural\s+networks|deep\s+learning|statistics|probability|linear\s+algebra|calculus|discrete\s+math|computer\s+science|software\s+engineering|algorithms|complexity|big\s+o|time\s+complexity|space\s+complexity|dynamic\s+programming|greedy|divide\s+and\s+conquer|backtracking|graph|tree|linked\s+list|stack|queue|hash\s+table|binary\s+tree|bst|heap|priority\s+queue|sorting\s+algorithms|search\s+algorithms|binary\s+search|linear\s+search|bubble\s+sort|quick\s+sort|merge\s+sort|insertion\s+sort|selection\s+sort|heap\s+sort|counting\s+sort|radix\s+sort|bucket\s+sort))'
    
    print(f"消息: '{message}'")
    print(f"正则表达式: {pattern}")
    
    match = re.search(pattern, message, re.IGNORECASE)
    if match and match.group(1):
        print(f"匹配成功: '{match.group(1).strip()}'")
    else:
        print("匹配失败")
        
        # 尝试简化版本
        simple_pattern = r'find\s+([a-zA-Z\s]+)\s+difficult'
        simple_match = re.search(simple_pattern, message, re.IGNORECASE)
        if simple_match and simple_match.group(1):
            print(f"简化版本匹配: '{simple_match.group(1).strip()}'")
        
        # 更简单的版本
        simpler_pattern = r'find\s+(.+?)\s+difficult'
        simpler_match = re.search(simpler_pattern, message, re.IGNORECASE)
        if simpler_match and simpler_match.group(1):
            print(f"更简版本匹配: '{simpler_match.group(1).strip()}'")

if __name__ == "__main__":
    debug_regex()