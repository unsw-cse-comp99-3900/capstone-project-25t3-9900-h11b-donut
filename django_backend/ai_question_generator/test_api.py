"""
AI Question Generator & Grader - API测试脚本
测试AI题目生成和评分的完整流程

使用方法:
1. 确保Django服务器正在运行: python manage.py runserver
2. 确保已通过AdminManageCourse页面上传课程题目（用作AI生成示例）
3. 确保.env中配置了GEMINI_API_KEY
4. 运行测试: python ai_question_generator/test_api.py
"""
import requests
import json
import sys
import time

# 配置
BASE_URL = 'http://localhost:8000/api/ai'
COURSE_CODE = 'COMP9900'
STUDENT_ID = 'z1234567'

# 颜色输出（Windows兼容）
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title):
    separator = "=" * 60
    print(f'
{Colors.BOLD}{Colors.CYAN}{separator}{Colors.END}')
    print(f'{Colors.BOLD}{Colors.CYAN}  {title}{Colors.END}')
    print(f'{Colors.BOLD}{Colors.CYAN}{separator}{Colors.END}')

def print_success(text):
    print(f'{Colors.GREEN}SUCCESS: {text}{Colors.END}')

def print_error(text):
    print(f'{Colors.RED}ERROR: {text}{Colors.END}')

def print_info(text):
    print(f'{Colors.BLUE}INFO: {text}{Colors.END}')

def print_warning(text):
    print(f'{Colors.YELLOW}WARNING: {text}{Colors.END}')


def test_generate_questions():
    """测试AI生成题目"""
    print_section('2. 测试AI生成题目')
    
    url = f'{BASE_URL}/questions/generate'
    data = {
        "course_code": COURSE_CODE,
        "topic": "Neural Networks in Deep Learning",
        "difficulty": "medium",
        "count": 5,
        "mcq_count": 3,
        "short_answer_count": 2
    }
    
    print_info(f'POST {url}')
    print_info(f'主题: {data["topic"]}')
    print_info(f'难度: {data["difficulty"]}, 题目数: {data["count"]}')
    print_warning('AI生成中，请等待10-15秒...')
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print_info(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_success(f'成功生成 {result["total_questions"]} 道题目')
                print_success(f'Session ID: {result["session_id"]}')
                
                # 显示题目预览
                for idx, q in enumerate(result['questions'], 1):
                    print(f'
  题目 {idx}:')
                    print(f'  类型: {q["type"]}')
                    print(f'  问题: {q["question"][:80]}...')
                    if q['type'] == 'mcq':
                        print(f'  选项数: {len(q.get("options", []))}')
                    print(f'  分值: {q.get("score", 10)} 分')
                    print(f'  DB ID: {q.get("db_id")}')
                
                return True, result
            else:
                print_error(f'生成失败: {result.get("error")}')
                if 'traceback' in result:
                    print(f'
{result["traceback"]}')
                return False, result
        else:
            print_error(f'HTTP错误: {response.status_code}')
            print_error(response.text)
            return False, {}
    except requests.exceptions.Timeout:
        print_error('请求超时！AI生成时间过长')
        return False, {}
    except Exception as e:
        print_error(f'请求失败: {e}')
        return False, {}


def test_submit_answers(session_id, questions):
    """测试提交答案并评分"""
    print_section('2. 测试提交答案并AI评分')
    
    url = f'{BASE_URL}/answers/submit'
    
    # 构造测试答案（模拟真实学生答题）
    answers = []
    for idx, q in enumerate(questions):
        if q['type'] == 'mcq':
            # 第一道选择题正确，其他选A
            if idx == 0 and 'correct_answer' in q:
                answer = q['correct_answer']
            else:
                answer = 'A'
        else:
            # 简答题给部分正确的答案
            answer = "Neural networks use layers of interconnected nodes to process data. The learning rate controls how quickly the model learns. If too high, it may overshoot optimal values. If too low, training is very slow."
        
        answers.append({
            "question_db_id": q['db_id'],
            "answer": answer
        })
    
    data = {
        "session_id": session_id,
        "student_id": STUDENT_ID,
        "answers": answers
    }
    
    print_info(f'POST {url}')
    print_info(f'学生ID: {STUDENT_ID}')
    print_info(f'提交 {len(answers)} 个答案')
    print_warning('AI评分中，请等待15-30秒...')
    
    try:
        response = requests.post(url, json=data, timeout=120)
        print_info(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_success('评分完成！')
                print_success(f'总分: {result["total_score"]:.1f}/{result["total_max_score"]} ({result["percentage"]:.1f}%)')
                
                # 显示详细评分
                for idx, r in enumerate(result['grading_results'], 1):
                    print(f'
  题目 {idx} 评分:')
                    print(f'  类型: {r["type"]}')
                    print(f'  学生答案: {r["student_answer"][:60]}...')
                    print(f'  得分: {r["score"]:.1f}/{r["max_score"]}')
                    
                    if r.get('is_correct') is not None:
                        status = 'CORRECT' if r["is_correct"] else 'INCORRECT'
                        print(f'  结果: {status}')
                        if not r["is_correct"]:
                            print(f'  正确答案: {r.get("correct_answer")}')
                    
                    if r.get('breakdown'):
                        print(f'  评分细节:')
                        for criterion, score in r['breakdown'].items():
                            print(f'    - {criterion}: {score}')
                    
                    if r.get('hint'):
                        print(f'  提示: {r["hint"][:100]}...')
                    if r.get('solution'):
                        print(f'  解答: {r["solution"][:100]}...')
                
                return True, result
            else:
                print_error(f'评分失败: {result.get("error")}')
                if 'traceback' in result:
                    print(f'
{result["traceback"]}')
                return False, result
        else:
            print_error(f'HTTP错误: {response.status_code}')
            print_error(response.text)
            return False, {}
    except requests.exceptions.Timeout:
        print_error('请求超时！AI评分时间过长')
        return False, {}
    except Exception as e:
        print_error(f'请求失败: {e}')
        return False, {}


def test_get_student_results():
    """测试获取学生历史成绩"""
    print_section('3. 测试获取学生历史成绩')
    
    url = f'{BASE_URL}/results?student_id={STUDENT_ID}'
    
    print_info(f'GET {url}')
    
    try:
        response = requests.get(url, timeout=10)
        print_info(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                results = result.get('results', [])
                print_success(f'找到 {len(results)} 条答题记录')
                
                # 显示最近3条记录
                for idx, record in enumerate(results[:3], 1):
                    print(f'
  记录 {idx}:')
                    print(f'  Session ID: {record.get("session_id")}')
                    print(f'  题目ID: {record.get("question_id")}')
                    grading = record.get('grading_result', {})
                    print(f'  得分: {grading.get("score")}/{grading.get("max_score")}')
                    print(f'  提交时间: {record.get("submitted_at")}')
                
                return True, result
            else:
                print_error(f'查询失败: {result.get("error")}')
                return False, result
        else:
            print_error(f'HTTP错误: {response.status_code}')
            return False, {}
    except Exception as e:
        print_error(f'请求失败: {e}')
        return False, {}


def main():
    """运行完整测试流程"""
    print_section('AI Question Generator & Grader - 完整API测试')
    print_info(f'Base URL: {BASE_URL}')
    print_info(f'Course Code: {COURSE_CODE}')
    print_info(f'Student ID: {STUDENT_ID}')
    
    print_info('\n测试前准备:')
    print_info('1. 确保Django服务器正在运行')
    print_info('2. 确保已通过AdminManageCourse页面上传课程题目')
    print_info('3. 确保.env中配置了GEMINI_API_KEY')
    print_info('\n开始测试...\n')
    
    try:
        # 测试1: AI生成题目
        success, gen_result = test_generate_questions()
        if not success or not gen_result.get('success'):
            print_error('\n测试1失败！请确保:')
            print_error('  1. 已通过AdminManageCourse页面上传 COMP9900 课程的题目')
            print_error('  2. .env中已配置 GEMINI_API_KEY')
            return
        
        session_id = gen_result['session_id']
        questions = gen_result['questions']
        
        time.sleep(2)
        
        # 测试2: 提交答案并AI评分
        success, grade_result = test_submit_answers(session_id, questions)
        if not success:
            print_warning('\n测试2失败，但继续执行')
        
        time.sleep(1)
        
        # 测试3: 获取历史成绩
        test_get_student_results()
        
        # 总结
        print_section('测试完成')
        print_success('所有API测试已完成！')
        print_info('你可以在Django Admin中查看数据库记录:')
        print_info('访问: http://localhost:8000/admin/ai_question_generator/')
        
    except KeyboardInterrupt:
        print_warning('\n\n测试被用户中断')
    except Exception as e:
        print_error(f'\n测试过程中发生错误: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
