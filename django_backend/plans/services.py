"""
学习计划服务模块
处理AI生成结果到数据库存储的映射和保存逻辑
"""
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from django.utils import timezone
from django.db import transaction
from .models import StudyPlan, StudyPlanItem
from stu_accounts.models import StudentAccount
import calendar


def week_monday(base_date: date = None, offset: int = 0) -> date:
    """获取指定日期所在周的周一"""
    if base_date is None:
        base_date = date.today()
    
    # Python weekday(): Monday=0 .. Sunday=6
    monday = base_date - timedelta(days=base_date.weekday())
    monday += timedelta(days=offset * 7)
    return monday


def map_ai_result_to_weekly_format(ai_result: Dict[str, Any], timezone_str: str = 'Australia/Sydney') -> Dict[int, List[Dict]]:
    """
    将AI生成的计划结果映射为前端所需的周计划格式
    
    Args:
        ai_result: AI模块返回的完整结果
        timezone_str: 用户时区
        
    Returns:
        以week_offset为键的周计划字典
    """
    weekly_plans = {}
    
    if not ai_result or "days" not in ai_result:
        print("⚠️ [MAP_AI_RESULT] AI结果中缺少days数据")
        return weekly_plans
    
    days = ai_result["days"]
    if not days:
        print("⚠️ [MAP_AI_RESULT] days数组为空")
        return weekly_plans
    
    # 计算基准周（使用第一天所在周的周一）
    first_day = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    base_monday = week_monday(first_day)
    
    # 任务元信息索引
    meta_by_task_id = {}
    if ai_result.get("aiSummary") and "tasks" in ai_result["aiSummary"]:
        for task in ai_result["aiSummary"]["tasks"]:
            task_id = task.get("taskId", "")
            meta_by_task_id[task_id] = {
                "taskTitle": task.get("taskTitle", task_id),
                "partsCount": len(task.get("parts", [])) if isinstance(task.get("parts"), list) else 0,
            }
    
    # 遍历每天的任务块
    for day in days:
        day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
        week_offset = (day_date - base_monday).days // 7
        
        if week_offset not in weekly_plans:
            weekly_plans[week_offset] = []
        
        for block in day.get("blocks", []):
            task_id = block.get("taskId", "")
            course_code = task_id.split("_")[0] if "_" in task_id else task_id
            
            meta = meta_by_task_id.get(task_id, {"taskTitle": task_id, "partsCount": 0})
            
            # 从partId提取序号
            part_id = str(block.get("partId", ""))
            part_index = None
            if part_id:
                import re
                match = re.search(r'\d+', part_id)
                if match:
                    part_index = int(match.group())
            
            # 构造前端所需的计划项格式
            plan_item = {
                "id": f"{course_code}-{task_id}" + (f"-{part_index}" if part_index is not None else ""),
                "courseId": course_code,
                "courseTitle": meta["taskTitle"],
                "partTitle": block.get("title", ""),
                "minutes": block.get("minutes", 0),
                "date": day["date"],
                "color": "#888",  # 默认颜色，实际应该从coursesStore获取
                "completed": False,
                "partIndex": part_index,
                "partsCount": meta["partsCount"],
            }
            
            weekly_plans[week_offset].append(plan_item)
    
    print(f"📅 [MAP_AI_RESULT] 映射完成，生成了 {len(weekly_plans)} 周的计划")
    for offset, items in weekly_plans.items():
        print(f"   Week {offset}: {len(items)} 个任务项")
    
    return weekly_plans


def _save_plan_to_database_directly(student: StudentAccount, weekly_plans: Dict[int, List[Dict]], ai_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    直接将AI生成的周计划保存到数据库
    
    Args:
        student: 学生账户对象
        weekly_plans: 周计划数据 (week_offset -> plan_items)
        ai_details: AI生成的详细内容
        
    Returns:
        保存结果 {"success": bool, "plan_id": int, "error": str}
    """
    try:
        result = {"success": True, "saved": [], "plan_id": None, "error": None}
        
        # 逐个week_offset处理
        for offset, items in weekly_plans.items():
            if not items:
                continue
            
            week_monday_date = week_monday(offset=offset)
            
            with transaction.atomic():
                # 创建或更新StudyPlan记录
                meta_data = {
                    "hasAIGeneration": True,
                    "aiDetails": ai_details,
                    "generationReason": ai_details.get("generationReason", ""),
                    "generationTime": ai_details.get("generationTime", ""),
                }
                
                plan, created = StudyPlan.objects.update_or_create(
                    student_id=student.student_id,
                    week_start_date=week_monday_date,
                    defaults={
                        "week_offset": offset,
                        "tz": "Australia/Sydney",
                        "source": "ai",
                        "meta": meta_data,
                    },
                )
                
                # 如果是更新操作，需要手动更新meta字段
                if not created:
                    print(f"🔄 [SAVE_PLAN] 检测到更新操作，计划ID: {plan.id}")
                    print(f"🔄 [SAVE_PLAN] 准备更新的meta数据: {meta_data}")
                    updated_count = StudyPlan.objects.filter(id=plan.id).update(
                        week_offset=offset,
                        tz="Australia/Sydney",
                        source="ai",
                        meta=meta_data
                    )
                    print(f"🔄 [SAVE_PLAN] 更新了 {updated_count} 条记录的meta数据")
                else:
                    print(f"✅ [SAVE_PLAN] 创建了新计划，ID: {plan.id}")
                
                # 清空旧的计划项
                StudyPlanItem.objects.filter(plan=plan).delete()
                
                # 批量创建新的计划项
                plan_items = []
                for item in items:
                    try:
                        # 提取task_id
                        task_id = None
                        parts = str(item.get("id", "")).split("-")
                        if len(parts) >= 2:
                            task_id = parts[1]
                        
                        plan_items.append(StudyPlanItem(
                            plan=plan,
                            external_item_id=item.get("id", ""),
                            course_code=item.get("courseId", ""),
                            course_title=item.get("courseTitle", ""),
                            scheduled_date=datetime.strptime(item["date"], "%Y-%m-%d").date() if item.get("date") else week_monday_date,
                            minutes=int(item.get("minutes", 0)),
                            part_index=item.get("partIndex", 0),
                            parts_count=item.get("partsCount", 0),
                            part_title=item.get("partTitle", ""),
                            color=item.get("color", "#888"),
                            completed=item.get("completed", False),
                            completed_at=timezone.now() if item.get("completed") else None,
                            task_id=task_id,
                        ))
                    except Exception as item_error:
                        print(f"⚠️ 处理计划项时出错: {item_error}, 项数据: {item}")
                        continue
                
                if plan_items:
                    StudyPlanItem.objects.bulk_create(plan_items)
                
                result["saved"].append({
                    "offset": offset,
                    "week_start_date": week_monday_date.isoformat(),
                    "plan_id": plan.id,
                    "created": created,
                    "items": len(plan_items),
                })
                
                # 记录第一个计划的ID
                if result["plan_id"] is None:
                    result["plan_id"] = plan.id
        
        print(f"✅ [SAVE_PLAN_DIRECTLY] 成功保存 {len(result['saved'])} 个周计划")
        return result
        
    except Exception as e:
        error_msg = f"保存计划到数据库失败: {str(e)}"
        print(f"❌ [SAVE_PLAN_DIRECTLY] {error_msg}")
        return {"success": False, "error": error_msg, "plan_id": None}