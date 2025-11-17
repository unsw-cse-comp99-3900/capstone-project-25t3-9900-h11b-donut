import json
from pathlib import Path
from datetime import date, timedelta
from .plan_generator import generate_plan

today = date.today()
AI_DIR = Path(__file__).resolve().parent

# 拼出 PDF 的绝对路径（不会受运行目录影响）
# COMP9417 - 机器学习课程
PDF_9417_A1 = (AI_DIR / "9417assignment1.pdf").as_posix()
PDF_9417_A2 = (AI_DIR / "9417assignment2.pdf").as_posix()
PDF_9417_A3 = (AI_DIR / "9417assignment3.pdf").as_posix()

# COMP9517 - 计算机视觉课程
PDF_9517_A1 = (AI_DIR / "9517assignment1.pdf").as_posix()
PDF_9517_A2 = (AI_DIR / "9517assignment2.pdf").as_posix()
PDF_9517_A3 = (AI_DIR / "9517assignment3.pdf").as_posix()

# COMP9900 - 软件工程课程
PDF_9900_A1 = (AI_DIR / "9900assignment1.pdf").as_posix()
PDF_9900_A2 = (AI_DIR / "9900assignment2.pdf").as_posix()
PDF_9900_A3 = (AI_DIR / "9900assignment3.pdf").as_posix()

tasks_meta = [
    # COMP9517 Assignment 1 - 最早截止 (2025-10-25)
    {
        "id": "9517_a1",
        "task": "COMP9517 - Assignment 1", 
        "dueDate": "2025-10-25",
        "detailPdfPath": PDF_9517_A1
    },
    # COMP9900 Assignment 1 - 第二早 (2025-10-30)
    {
        "id": "9900_a1",
        "task": "COMP9900 - Assignment 1",
        "dueDate": "2025-10-30", 
        "detailPdfPath": PDF_9900_A1
    },
    # COMP9417 Assignment 1 - 第三早 (2025-11-10)
    {
        "id": "9417_a1",
        "task": "COMP9417 - Assignment 1",
        "dueDate": "2025-11-10", 
        "detailPdfPath": PDF_9417_A1
    },
    # COMP9900 Assignment 2 - 同日 (2025-11-10)
    {
        "id": "9900_a2",
        "task": "COMP9900 - Assignment 2",
        "dueDate": "2025-11-10", 
        "detailPdfPath": PDF_9900_A2
    },
    # COMP9517 Assignment 2 - (2025-11-12)
    {
        "id": "9517_a2",
        "task": "COMP9517 - Assignment 2",
        "dueDate": "2025-11-12", 
        "detailPdfPath": PDF_9517_A2
    },
    # COMP9417 Assignment 2 - (2025-12-05)
    {
        "id": "9417_a2",
        "task": "COMP9417 - Assignment 2",
        "dueDate": "2025-12-05", 
        "detailPdfPath": PDF_9417_A2
    },
    # COMP9900 Assignment 3 - (2025-12-10)
    {
        "id": "9900_a3",
        "task": "COMP9900 - Assignment 3",
        "dueDate": "2025-12-10", 
        "detailPdfPath": PDF_9900_A3
    },
    # COMP9517 Assignment 3 - (2025-12-15)
    {
        "id": "9517_a3",
        "task": "COMP9517 - Assignment 3",
        "dueDate": "2025-12-15", 
        "detailPdfPath": PDF_9517_A3
    },
    # COMP9417 Assignment 3 - 最晚 (2025-12-30)
    {
        "id": "9417_a3",
        "task": "COMP9417 - Assignment 3",
        "dueDate": "2025-12-30", 
        "detailPdfPath": PDF_9417_A3
    }
]

preferences = {
    "daily_hour_cap": 3,     # 每日学习 3 小时
    "weekly_study_days": 5,  # 每周学习 5 天
    "avoid_days": [5, 6]     # 周六周日不学（0=Mon…6=Sun；仅放松阶梯第2步才使用）
}

if __name__ == "__main__":
    print("=== AI Module 测试 - 多课程多作业场景 ===")
    print("📚 课程设置:")
    print("  COMP9417 (机器学习): Assignment1(11-10) → Assignment2(12-05) → Assignment3(12-30)")
    print("  COMP9517 (计算机视觉): Assignment1(10-25) → Assignment2(11-12) → Assignment3(12-15)")
    print("  COMP9900 (软件工程): Assignment1(10-30) → Assignment2(11-10) → Assignment3(12-10)")
    print(f"\n📋 总共 {len(tasks_meta)} 个作业任务:")
    for i, meta in enumerate(tasks_meta, 1):
        print(f"  {i}. {meta['task']} (截止: {meta['dueDate']})")
    print(f"\n⚙️ 偏好设置: 每日{preferences['daily_hour_cap']}小时, 每周{preferences['weekly_study_days']}天, 避开周末")
    
    # 先测试 PDF 读取 (只显示前3个作为示例)
    print("\n=== PDF 内容读取测试 (前3个任务示例) ===")
    from .pdf_ingest import extract_text_from_pdf
    for i, meta in enumerate(tasks_meta[:3], 1):
        print(f"\n--- {meta['task']} ---")
        if meta.get("detailPdfPath"):
            try:
                pdf_text = extract_text_from_pdf(meta["detailPdfPath"])
                if pdf_text:
                    print(f"✅ PDF读取成功: {len(pdf_text)} 字符")
                    print(f"前200字符预览: {pdf_text[:200]}...")
                else:
                    print("❌ PDF 文本为空")
            except Exception as e:
                print(f"❌ PDF 读取失败: {e}")
        else:
            print("❌ 无 PDF 文件")
    
    # 测试 AI 摘要 (只分析前3个任务以节省时间)
    print("\n=== AI 摘要分析测试 (前3个任务) ===")
    from .llm_structures import summarize_task_details
    for i, meta in enumerate(tasks_meta[:3], 1):
        print(f"\n--- {meta['task']} AI 分析 ---")
        if meta.get("detailPdfPath"):
            try:
                pdf_text = extract_text_from_pdf(meta["detailPdfPath"])
                if pdf_text:
                    summary = summarize_task_details(meta["task"], meta["dueDate"], pdf_text)
                    if summary:
                        print(f"✅ AI 估算时长: {summary.get('estimatedHours', 'N/A')} 小时")
                        print(f"✅ AI 建议拆分: {len(summary.get('suggestedParts', []))} 个部分")
                        parts_preview = summary.get('suggestedParts', [])[:2]  # 只显示前2个部分
                        for j, part in enumerate(parts_preview, 1):
                            print(f"   Part{j}: {part.get('title', f'Part {j}')} ({part.get('minutes', 'N/A')}分钟)")
                    else:
                        print("❌ AI 摘要失败")
                else:
                    print("❌ PDF 文本为空")
            except Exception as e:
                print(f"❌ AI 分析失败: {e}")
    
    print("\n=== 开始生成完整计划 ===")
    out = generate_plan(preferences, tasks_meta)
    
    print("\n" + "="*80)
    print("🎯 每个 Assignment 的详细 AI 分析结果")
    print("="*80)
    if "aiSummary" in out and "tasks" in out["aiSummary"]:
        for i, task_info in enumerate(out["aiSummary"]["tasks"], 1):
            print(f"\n📋 【任务 {i}】{task_info['taskTitle']}")
            print(f"⏱️  总时长: {task_info['totalMinutes']} 分钟 ({task_info['totalMinutes']/60:.1f} 小时)")
            print(f"🤖 AI 说明: {task_info['explanation']}")
            print(f"🔧 拆分成 {len(task_info['parts'])} 个部分:")
            for j, part in enumerate(task_info['parts'], 1):
                print(f"   Part {j}: {part['title']}")
                print(f"           时长: {part['minutes']}分钟 ({part['percent']}%)")
                if part.get('notes'):
                    print(f"           备注: {part['notes']}")
            print("-" * 60)
    
    print("\n" + "="*80)
    print("📅 最终完整排程计划")
    print("="*80)
    if "days" in out:
        current_week_start = None
        for day_info in out["days"]:
            day_date = day_info["date"]
            from datetime import datetime
            day_obj = datetime.fromisoformat(day_date).date()
            week_start = day_obj - timedelta(days=day_obj.weekday())
            
            # 如果是新的一周，打印周标题
            if week_start != current_week_start:
                current_week_start = week_start
                week_end = week_start + timedelta(days=6)
                print(f"\n📆 第 {(week_start - datetime.fromisoformat('2025-10-13').date()).days // 7 + 1} 周: {week_start} 到 {week_end}")
                print("-" * 60)
            
            # 打印每日安排
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            weekday_name = weekday_names[day_obj.weekday()]
            
            if day_info["blocks"]:
                total_minutes = sum(block["minutes"] for block in day_info["blocks"])
                print(f"\n🗓️  {day_date} ({weekday_name}) - 总计 {total_minutes} 分钟 ({total_minutes/60:.1f} 小时)")
                for k, block in enumerate(day_info["blocks"], 1):
                    print(f"   {k}. {block['title']} ({block['minutes']}分钟)")
                    print(f"      任务ID: {block['taskId']} | Part ID: {block['partId']}")
            else:
                print(f"\n🗓️  {day_date} ({weekday_name}) - 休息日 ✨")
    
    print("\n" + "="*80)
    print("📊 排程统计摘要")
    print("="*80)
    if "taskSummary" in out:
        total_work_minutes = 0
        for task_summary in out["taskSummary"]:
            total_work_minutes += task_summary["totalMinutes"]
            print(f"📚 {task_summary['taskTitle']}: {task_summary['totalMinutes']}分钟 ({task_summary['totalMinutes']/60:.1f}小时)")
        
        print(f"\n🎯 总工作量: {total_work_minutes}分钟 ({total_work_minutes/60:.1f}小时)")
        
        # 计算工作日数
        work_days = len([day for day in out.get("days", []) if day["blocks"]])
        if work_days > 0:
            avg_per_day = total_work_minutes / work_days
            print(f"📈 工作天数: {work_days}天")
            print(f"📊 平均每日: {avg_per_day:.0f}分钟 ({avg_per_day/60:.1f}小时)")
        
        if "relaxation" in out:
            relaxation_status = {
                "none": "✅ 完全符合偏好设置",
                "expand-days-per-week": "⚠️ 扩展了每周学习天数",
                "allow-avoid-days": "⚠️ 使用了避开的日期",
                "max10h": "⚠️ 提升到每日10小时上限",
                "impossible": "❌ 无法安排"
            }
            print(f"🔧 调度状态: {relaxation_status.get(out['relaxation'], out['relaxation'])}")
    
    print("\n=== 完整计划结果 ===")
    print(json.dumps(out, indent=2, ensure_ascii=False))