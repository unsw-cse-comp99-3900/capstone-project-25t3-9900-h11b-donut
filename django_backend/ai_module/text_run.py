import json
from pathlib import Path
from datetime import date, timedelta
from .plan_generator import generate_plan

today = date.today()
AI_DIR = Path(__file__).resolve().parent


# COMP9417 
PDF_9417_A1 = (AI_DIR / "9417assignment1.pdf").as_posix()
PDF_9417_A2 = (AI_DIR / "9417assignment2.pdf").as_posix()
PDF_9417_A3 = (AI_DIR / "9417assignment3.pdf").as_posix()

# COMP9517
PDF_9517_A1 = (AI_DIR / "9517assignment1.pdf").as_posix()
PDF_9517_A2 = (AI_DIR / "9517assignment2.pdf").as_posix()
PDF_9517_A3 = (AI_DIR / "9517assignment3.pdf").as_posix()

# COMP9900
PDF_9900_A1 = (AI_DIR / "9900assignment1.pdf").as_posix()
PDF_9900_A2 = (AI_DIR / "9900assignment2.pdf").as_posix()
PDF_9900_A3 = (AI_DIR / "9900assignment3.pdf").as_posix()

tasks_meta = [
    # COMP9517 Assignment 1 - first due (2025-10-25)
    {
        "id": "9517_a1",
        "task": "COMP9517 - Assignment 1", 
        "dueDate": "2025-10-25",
        "detailPdfPath": PDF_9517_A1
    },
    # COMP9900 Assignment 1 - second due (2025-10-30)
    {
        "id": "9900_a1",
        "task": "COMP9900 - Assignment 1",
        "dueDate": "2025-10-30", 
        "detailPdfPath": PDF_9900_A1
    },
    # COMP9417 Assignment 1 - third due (2025-11-10)
    {
        "id": "9417_a1",
        "task": "COMP9417 - Assignment 1",
        "dueDate": "2025-11-10", 
        "detailPdfPath": PDF_9417_A1
    },
    # COMP9900 Assignment 2 - same day (2025-11-10)
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
    "daily_hour_cap": 3,     
    "weekly_study_days": 5,  
    "avoid_days": [5, 6]     
}

if __name__ == "__main__":
    print("=== AI Module Test - Multi-Course Multi-Assignment Scenario ===")
    print("📚 Course Setup:")
    print("  COMP9417 (Machine Learning): Assignment1(11-10) → Assignment2(12-05) → Assignment3(12-30)")
    print("  COMP9517 (Computer Vision): Assignment1(10-25) → Assignment2(11-12) → Assignment3(12-15)")
    print("  COMP9900 (Software Engineering): Assignment1(10-30) → Assignment2(11-10) → Assignment3(12-10)")
    print(f"\n📋 Total {len(tasks_meta)} assignment tasks:")
    for i, meta in enumerate(tasks_meta, 1):
        print(f"  {i}. {meta['task']} (Due: {meta['dueDate']})")

    print(f"\n⚙️ Preferences: {preferences['daily_hour_cap']} hours/day, {preferences['weekly_study_days']} study days/week, avoid weekends")

    print("\n=== PDF Content Extraction Test (First 3 Tasks Example) ===")
    from .pdf_ingest import extract_text_from_pdf
    for i, meta in enumerate(tasks_meta[:3], 1):
        print(f"\n--- {meta['task']} ---")
        if meta.get("detailPdfPath"):
            try:
                pdf_text = extract_text_from_pdf(meta["detailPdfPath"])
                if pdf_text:
                    print(f"✅ PDF read ok!: {len(pdf_text)} characters")
                    print(f"first 200 characters: {pdf_text[:200]}...")
                else:
                    print("❌ empty file")
            except Exception as e:
                print(f"❌ PDF read fail: {e}")
        else:
            print("❌ no file found")
    
    print("\n===AI Summary Analysis Test (First 3 Tasks) ===")
    from .llm_structures import summarize_task_details
    for i, meta in enumerate(tasks_meta[:3], 1):
        print(f"\n--- {meta['task']} AI analyze ---")
        if meta.get("detailPdfPath"):
            try:
                pdf_text = extract_text_from_pdf(meta["detailPdfPath"])
                if pdf_text:
                    summary = summarize_task_details(meta["task"], meta["dueDate"], pdf_text)
                    if summary:
                        print(f"✅ AI estimated hours: {summary.get('estimatedHours', 'N/A')} hours")
                        print(f"✅ AI suggestion allocation: {len(summary.get('suggestedParts', []))} parts")
                        parts_preview = summary.get('suggestedParts', [])[:2]  
                        for j, part in enumerate(parts_preview, 1):
                            print(f"   Part{j}: {part.get('title', f'Part {j}')} ({part.get('minutes', 'N/A')}mins)")
                    else:
                        print("❌ AI fail")
                else:
                    print("❌ PDF not found")
            except Exception as e:
                print(f"❌ AI fail to analyze: {e}")
    
    print("\n=== start generating plan ===")
    out = generate_plan(preferences, tasks_meta)
    
    print("\n" + "="*80)
    print("🎯 Detailed AI Analysis Results for Each Assignment")
    print("="*80)

    if "aiSummary" in out and "tasks" in out["aiSummary"]:
        for i, task_info in enumerate(out["aiSummary"]["tasks"], 1):
            print(f"\n📋 [Task {i}] {task_info['taskTitle']}")
            print(f"⏱️  Total Time: {task_info['totalMinutes']} minutes ({task_info['totalMinutes']/60:.1f} hours)")
            print(f"🤖 AI Explanation: {task_info['explanation']}")
            print(f"🔧 Split into {len(task_info['parts'])} parts:")
            for j, part in enumerate(task_info['parts'], 1):
                print(f"   Part {j}: {part['title']}")
                print(f"           Duration: {part['minutes']} minutes ({part['percent']}%)")
                if part.get('notes'):
                    print(f"           Notes: {part['notes']}")
            print("-" * 60)

    print("\n" + "="*80)
    print("📅 Final Complete Scheduled Plan")
    print("="*80)
    if "days" in out:
        current_week_start = None
        for day_info in out["days"]:
            day_date = day_info["date"]
            from datetime import datetime
            day_obj = datetime.fromisoformat(day_date).date()
            week_start = day_obj - timedelta(days=day_obj.weekday())
            
            if week_start != current_week_start:
                current_week_start = week_start
                week_end = week_start + timedelta(days=6)
                print(f"\n📆 第 {(week_start - datetime.fromisoformat('2025-10-13').date()).days // 7 + 1} 周: {week_start} 到 {week_end}")
                print("-" * 60)
            
            # every day plan
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
    print("📊 Scheduling Summary")
    print("="*80)

    if "taskSummary" in out:
        total_work_minutes = 0
        for task_summary in out["taskSummary"]:
            total_work_minutes += task_summary["totalMinutes"]
            print(f"📚 {task_summary['taskTitle']}: {task_summary['totalMinutes']} minutes ({task_summary['totalMinutes']/60:.1f} hours)")
        
        print(f"\n🎯 Total Workload: {total_work_minutes} minutes ({total_work_minutes/60:.1f} hours)")
        
        # Calculate number of working days
        work_days = len([day for day in out.get("days", []) if day["blocks"]])
        if work_days > 0:
            avg_per_day = total_work_minutes / work_days
            print(f"📈 Working Days: {work_days} days")
            print(f"📊 Average per Day: {avg_per_day:.0f} minutes ({avg_per_day/60:.1f} hours)")
        
        if "relaxation" in out:
            relaxation_status = {
                "none": "✅ Fully satisfies preference settings",
                "expand-days-per-week": "⚠️ Expanded weekly study days",
                "allow-avoid-days": "⚠️ Used avoided dates",
                "max10h": "⚠️ Increased to the 10-hour daily limit",
                "impossible": "❌ Unable to schedule"
            }
            print(f"🔧 Scheduling Status: {relaxation_status.get(out['relaxation'], out['relaxation'])}")

    print("\n=== Complete Plan Output ===")
    print(json.dumps(out, indent=2, ensure_ascii=False))