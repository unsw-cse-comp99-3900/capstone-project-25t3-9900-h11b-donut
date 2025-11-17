from django.test import TestCase, Client
from datetime import datetime, timedelta
import base64, json

# 我们直接引用 courses.views 中的内存原型存储，注入模拟数据
from courses.views import MY_COURSES_BY_STUDENT, TASKS_BY_COURSE

def make_token(student_id: str) -> str:
    """生成与 utils.auth.make_token 一致的简单 Base64 Token"""
    payload = json.dumps({"student_id": student_id}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

class PlansAndTasksMockTests(TestCase):
    """
    使用纯内存模拟数据测试：
    - /api/courses/{id}/tasks 接口是否返回任务（带 courseId）
    - /api/plans/weekly/{offset} 是否返回已生成 parts（字段完整）
    """

    def setUp(self):
        self.client = Client()
        self.sid = "S1234567"
        self.token = make_token(self.sid)
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

        # 注入“我的课程”
        MY_COURSES_BY_STUDENT[self.sid] = ["COMP9900"]

        # 注入课程任务（与前端 CourseDetail 显示字段匹配）
        TASKS_BY_COURSE["COMP9900"] = [
            {
                "id": "1",
                "title": "Mock Proposal",
                "deadline": "2025-12-31",
                "brief": "Write a short proposal",
                "percentContribution": 30,
            },
            {
                "id": "2",
                "title": "Mock Report",
                "deadline": "2025-11-20",
                "brief": "Mid-term progress report",
                "percentContribution": 70,
            },
        ]

    def test_tasks_endpoint_returns_course_tasks(self):
        """验证 /api/courses/COMP9900/tasks 返回任务列表且包含 courseId"""
        resp = self.client.get("/api/courses/COMP9900/tasks", **self.auth)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"), f"payload={payload}")
        tasks = payload.get("data") or []
        self.assertGreater(len(tasks), 0, "任务列表不应为空")

        # 验证字段
        first = tasks[0]
        for key in ("id", "title", "deadline", "brief", "percentContribution", "courseId"):
            self.assertIn(key, first, f"缺少字段: {key}")

        # 断言 courseId 为 COMP9900
        self.assertEqual(first["courseId"], "COMP9900")

    def test_weekly_plan_returns_parts(self):
        """验证 /api/plans/weekly/0 返回计划 parts 并字段完整"""
        resp = self.client.get("/api/plans/weekly/0", **self.auth)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"), f"payload={payload}")
        items = payload.get("data") or []
        self.assertGreater(len(items), 0, "计划项不应为空")

        # 检查字段完整性
        required_keys = [
            "id", "courseId", "courseTitle", "partTitle",
            "minutes", "date", "color", "completed",
            "partIndex", "partsCount",
        ]
        for it in items:
            for k in required_keys:
                self.assertIn(k, it, f"计划项缺少字段: {k} -> {it}")

        # 验证日期处于当前周（Mon-Sun）
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())  # Monday=0
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

        def parse_date(dstr: str) -> datetime:
            return datetime.strptime(dstr, "%Y-%m-%d")

        for it in items[:7]:  # 抽样前 7 个项进行周内校验
            d = parse_date(it["date"])
            self.assertTrue(monday <= d <= sunday, f"日期应在本周内: {it['date']}")

        # 示例输出结构（仅用于文档说明，不参与断言）
        # items[0] 可能类似：
        # {
        #   "id": "COMP9900-1",
        #   "courseId": "COMP9900",
        #   "courseTitle": "COMP9900 - Mock Proposal",
        #   "partTitle": "Part 1 - Preparation",
        #   "minutes": 30,
        #   "date": "2025-10-14",
        #   "color": "#F6B48E",
        #   "completed": False,
        #   "partIndex": 1,
        #   "partsCount": 3
        # }

    def test_material_download_status(self):
        """
        材料下载接口：/api/materials/comp9900-coach-pdf/download
        若 components 目录存在该 PDF，返回 200；否则返回 404。
        两者均表示接口工作正常（不存在文件时给出清晰 404）。
        """
        resp = self.client.get("/api/materials/comp9900-coach-pdf/download", **self.auth)
        self.assertIn(resp.status_code, (200, 404), f"unexpected status: {resp.status_code}")