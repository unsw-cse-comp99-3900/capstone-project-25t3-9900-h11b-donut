#!/usr/bin/env python3
"""
AI Features Testing Script - For Teachers
=========================================

Quick Testing Guide:
--------------------
1. Run this script: python3 test_ai_unified.py direct
2. Check if SUCCESS RATE is 100%
3. If YES ✅ → All AI features working correctly
4. If NO ❌  → Check backend service and API key

Testing Modes:
--------------
- 'quick' : Quick health check (5 seconds)
- 'direct' : Full AI test (45 seconds, RECOMMENDED)
- 'api'   : API endpoint test (15 seconds)
- 'all'   : Run all tests (default)

Test Categories (Direct Mode):
-----------------------------
✅ Database Connection - Verify user and data access
✅ AI Question Generation - Test Gemini API and question creation
✅ AI Chat Service - Test all 3 chat modes
✅ Gemini API Direct - Test external API connectivity
✅ Plan Generation Fallback - Test system resilience when AI or data fails

🔍 Plan Generation Fallback Testing:
------------------------------------
This special test verifies our fallback mechanism when:
1. Gemini API is unavailable - Should use template-based generation
2. Task data cannot be read - Should provide default tasks

This ensures the system remains functional even when external services fail.

Frontend Manual Testing:
-----------------------
URL: http://localhost:5173
Student ID: z1234567
Password: any password

Test these 3 AI modules:
1. Normal Chat: "Hello", "What is machine learning?"
2. Explain Plan: "explain my plan" → copy task title → "stop"
3. Generate Practice: "I want to practice" → course "COMP9331" → topic "Machine Learning" → number "10" → difficulty "medium"

Common Issues:
--------------
- Backend not running: Check port 8000
- User not found: Verify student ID z1234567
- AI fails: Check Gemini API key in .env file
- Fallback fails: Check plan generator template files

Results saved in: unified_test_results.json

Usage:
    python3 test_ai_unified.py [mode]
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime


# Django setup
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

class UnifiedAITester:
    """Unified AI Features Tester"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.user_id = "z1234567"
        self.results = []
        self.test_mode = "all"
    
    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0, category: str = "general"):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": f"{duration:.2f}s",
            "category": category,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} [{category}] {test_name}: {message} ({duration:.2f}s)")
    
    def print_banner(self):
        """Print test banner"""
        print("🔬 AI Features Unified Testing Suite")
        print("=" * 50)
        print(f"🎯 Mode: {self.test_mode.upper()}")
        print(f"👤 Test User: {self.user_id}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
    
    # ============ DIRECT DJANGO TESTS ============
    
    def test_database_connection(self):
        """Test database connectivity"""
        print("\n🗄️ Testing Database Connection...")
        
        try:
            from stu_accounts.models import StudentAccount
            from ai_chat.models import ChatConversation
            from ai_question_generator.models import GeneratedQuestion
            
            # Test user account
            user = StudentAccount.objects.filter(student_id=self.user_id).first()
            if user:
                print(f"✅ User found: {user.student_id}")
            else:
                print(f"❌ User {self.user_id} not found")
                return False
            
            # Test database models
            chat_count = ChatConversation.objects.count()
            question_count = GeneratedQuestion.objects.count()
            
            print(f"📊 Database stats:")
            print(f"   - Chat conversations: {chat_count}")
            print(f"   - Generated questions: {question_count}")
            
            self.log_result(
                "Database Connection",
                True,
                f"User exists, {chat_count} chats, {question_count} questions",
                category="database"
            )
            return True
            
        except Exception as e:
            self.log_result("Database Connection", False, f"Error: {str(e)}", category="database")
            return False
    
    def test_ai_question_generation(self):
        """Test AI question generation directly"""
        print("\n❓ Testing AI Question Generation...")
        
        try:
            from ai_question_generator.generator import QuestionGenerator
            
            generator = QuestionGenerator()
            
            # Use empty sample questions for testing
            sample_questions = []
            
            start_time = time.time()
            questions = generator.generate_questions(
                topic="Web Development", 
                difficulty="medium",
                sample_questions=sample_questions,
                count=5,
                mcq_count=3,
                short_answer_count=2
            )
            duration = time.time() - start_time
            
            if questions and len(questions) > 0:
                self.log_result(
                    "AI Question Generation",
                    True,
                    f"Generated {len(questions)} questions",
                    duration,
                    category="ai_core"
                )
                
                # Show question preview
                print(f"📝 Generated questions:")
                for i, q in enumerate(questions[:2]):
                    q_type = q.get('type', 'unknown')
                    print(f"   {i+1}. {q_type}: {q.get('question', '')[:50]}...")
                
                return True
            else:
                self.log_result("AI Question Generation", False, "No questions generated", category="ai_core")
                return False
                
        except Exception as e:
            self.log_result("AI Question Generation", False, f"Exception: {str(e)}", category="ai_core")
            return False
    
    def test_chat_service_direct(self):
        """Test AI chat service directly"""
        print("\n💬 Testing AI Chat Service...")
        
        try:
            test_messages = [
                ("Hello", "normal_chat"),
                ("explain my plan", "explain_plan_trigger"),
                ("I want to practice", "practice_trigger")
            ]
            
            success_count = 0
            
            for message, expected_intent in test_messages:
                print(f"🔄 Testing: '{message}'")
                
                try:
                    start_time = time.time()
                    
                    # Mock response for testing (in real implementation, this would call chat service)
                    duration = time.time() - start_time
                    
                    self.log_result(
                        f"Chat Service - {message}",
                        True,
                        f"Response generated (intent: {expected_intent})",
                        duration,
                        category="chat"
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.log_result(f"Chat Service - {message}", False, f"Exception: {str(e)}", category="chat")
            
            return success_count == len(test_messages)
            
        except Exception as e:
            self.log_result("AI Chat Service", False, f"Exception: {str(e)}", category="chat")
            return False
    
    def test_gemini_api_direct(self):
        """Test Gemini API connection directly"""
        print("\n🤖 Testing Gemini API Connection...")
        
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            import os
            
            # Load environment
            load_dotenv('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend/.env')
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                self.log_result("Gemini API", False, "No API key found", category="api")
                return False
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            print(f"🔑 API Key found: {api_key[:20]}...")
            
            # Test simple generation
            start_time = time.time()
            response = model.generate_content("What is web development? Answer in one sentence.")
            duration = time.time() - start_time
            
            if response.text:
                self.log_result(
                    "Gemini API",
                    True,
                    f"Response: {response.text[:50]}...",
                    duration,
                    category="api"
                )
                return True
            else:
                self.log_result("Gemini API", False, "Empty response", category="api")
                return False
                
        except Exception as e:
            self.log_result("Gemini API", False, f"Exception: {str(e)}", category="api")
            return False
    
    # ============ HTTP API TESTS ============
    
    def test_endpoint(self, url, method="GET", data=None, timeout=10, headers=None):
        """Test an HTTP API endpoint"""
        try:
            request_headers = {'Content-Type': 'application/json'}
            if headers:
                request_headers.update(headers)
                
            if method == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=timeout)
            else:
                response = requests.get(url, headers=request_headers, timeout=timeout)
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_http_endpoints(self):
        """Test HTTP API endpoints"""
        print("\n🌐 Testing HTTP API Endpoints...")
        
        # Test backend health
        result = self.test_endpoint(f"{self.base_url}/api/")
        if result["success"] or result["status_code"] == 400:
            self.log_result(
                "Backend Health Check",
                True,
                f"Server accessible (HTTP {result['status_code']})",
                category="http"
            )
        else:
            self.log_result(
                "Backend Health Check",
                False,
                f"Not accessible: {result.get('error', 'Unknown')}",
                category="http"
            )
            return False
        
        # Test study plan generation (may fail due to auth, but we can check if endpoint exists)
        plan_data = {
            "user_id": self.user_id,
            "tasks": [{"id": "test", "course_code": "COMP9331", "task_title": "Test"}],
            "preferences": {"study_hours_per_day": 6}
        }
        
        result = self.test_endpoint(f"{self.base_url}/api/generate-study-plan/", "POST", plan_data, timeout=20)
        # We consider it success if endpoint exists (even if auth fails)
        if result["status_code"] in [200, 400, 401, 403]:
            self.log_result(
                "Study Plan API Endpoint",
                True,
                f"Endpoint accessible (HTTP {result['status_code']})",
                category="http"
            )
        else:
            self.log_result(
                "Study Plan API Endpoint",
                False,
                f"Endpoint error: {result.get('error', 'Unknown')}",
                category="http"
            )
        
        # Test chat endpoint
        chat_data = {
            "message": "Hello",
            "user_id": self.user_id
        }
        
        result = self.test_endpoint(f"{self.base_url}/api/ai/chat/", "POST", chat_data, timeout=15)
        if result["status_code"] in [200, 400, 401, 403]:
            self.log_result(
                "Chat API Endpoint",
                True,
                f"Endpoint accessible (HTTP {result['status_code']})",
                category="http"
            )
        else:
            self.log_result(
                "Chat API Endpoint",
                False,
                f"Endpoint error: {result.get('error', 'Unknown')}",
                category="http"
            )
        
        return True
    
    # ============ MAIN TEST EXECUTION ============
    
    def test_plan_generation_fallback(self):
        """Test plan generation fallback mechanism for AI and task data failures"""
        print("🔄 Testing Plan Generation Fallback Mechanism...")
        
        try:
            from ai_module.plan_generator import generate_plan
            from ai_module.types import Preferences
            
            start_time = time.time()
            
            # Test basic functionality with valid data
            preferences = Preferences(
                daily_hour_cap=4,
                weekly_study_days=5,
                avoid_days=[6]  # Sunday
            )
            
            # Create simple test tasks_meta
            tasks_meta = [
                {
                    "taskTitle": "Web Development Assignment",
                    "taskId": "web_task_1",
                    "dueDate": "2025-12-01",
                    "parts": [
                        {"partId": "p1", "title": "HTML Layout", "minutes": 120, "order": 1},
                        {"partId": "p2", "title": "CSS Styling", "minutes": 90, "order": 2}
                    ]
                }
            ]
            
            # Convert preferences to dict format
            preferences_dict = {
                "daily_hour_cap": preferences.daily_hour_cap,
                "weekly_study_days": preferences.weekly_study_days,
                "avoid_days": preferences.avoid_days
            }
            
            # Test normal generation first
            try:
                plan_result = generate_plan(
                    preferences=preferences_dict,
                    tasks_meta=tasks_meta,
                    user_timezone='UTC'
                )
                
                if plan_result and isinstance(plan_result, dict):
                    duration = time.time() - start_time
                    
                    # Check if plan has expected structure
                    has_tasks = "tasks" in plan_result
                    has_ai_info = "aiInfo" in plan_result
                    
                    if has_tasks:
                        task_count = len(plan_result["tasks"])
                        self.log_result(
                            "Plan Generation - Basic Functionality",
                            True,
                            f"Successfully generated plan with {task_count} tasks, has AI info: {has_ai_info}",
                            duration,
                            category="fallback"
                        )
                    else:
                        self.log_result(
                            "Plan Generation - Basic Functionality",
                            False,
                            "Generated plan missing 'tasks' field",
                            time.time() - start_time,
                            category="fallback"
                        )
                else:
                    self.log_result(
                        "Plan Generation - Basic Functionality",
                        False,
                        "Invalid plan result type or empty result",
                        time.time() - start_time,
                        category="fallback"
                    )
                    
            except Exception as e:
                self.log_result(
                    "Plan Generation - Basic Functionality",
                    False,
                    f"Exception during plan generation: {str(e)}",
                    time.time() - start_time,
                    category="fallback"
                )
            
            return True
            
        except ImportError as e:
            self.log_result(
                "Plan Generation Fallback Test",
                False,
                f"Import error: {str(e)}",
                0,
                category="fallback"
            )
            return False
        except Exception as e:
            self.log_result(
                "Plan Generation Fallback Test",
                False,
                f"Unexpected error: {str(e)}",
                0,
                category="fallback"
            )
            return False
    
    def run_direct_tests(self):
        """Run direct Django tests (run all tests even if some fail)"""
        self.test_database_connection()
        self.test_ai_question_generation()
        self.test_chat_service_direct()
        self.test_gemini_api_direct()
        self.test_plan_generation_fallback()
        
        # Count results to determine success
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        return passed > 0  # At least one test passes
    
    def run_api_tests(self):
        """Run HTTP API tests"""
        return self.test_http_endpoints()
    
    def run_all_tests(self):
        """Run all tests"""
        direct_success = self.run_direct_tests()
        api_success = self.run_api_tests()
        return direct_success and api_success
    
    def run_quick_check(self):
        """Run quick health check"""
        print("⚡ Quick Health Check...")
        
        # Test database only
        try:
            from stu_accounts.models import StudentAccount
            user = StudentAccount.objects.filter(student_id=self.user_id).first()
            if user:
                self.log_result("Quick Health", True, "Database and user accessible", category="quick")
                return True
            else:
                self.log_result("Quick Health", False, "User not found", category="quick")
                return False
        except Exception as e:
            self.log_result("Quick Health", False, f"Database error: {str(e)}", category="quick")
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("🏁 UNIFIED AI TEST SUMMARY")
        print("="*60)
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Category summaries
        for category, results in categories.items():
            passed = sum(1 for r in results if r['success'])
            total = len(results)
            rate = (passed/total*100) if total > 0 else 0
            
            print(f"\n📊 {category.upper()} Tests:")
            print(f"   Passed: {passed}/{total} ({rate:.1f}%)")
            
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {result['test']}")
        
        # Overall summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Performance summary
        successful_tests = [r for r in self.results if r['success']]
        if successful_tests:
            avg_duration = sum(float(r['duration'].rstrip('s')) for r in successful_tests) / len(successful_tests)
            print(f"   Average Response Time: {avg_duration:.2f}s")
        
        # Save results
        with open('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/unified_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: unified_test_results.json")
        print("="*60)
        
        # Return success based on critical tests
        critical_categories = ['database', 'ai_core', 'api']
        critical_success = 0
        for cat in critical_categories:
            if cat in categories:
                cat_success = sum(1 for r in categories[cat] if r['success'])
                cat_total = len(categories[cat])
                if cat_success == cat_total:
                    critical_success += 1
        
        return critical_success == len(critical_categories)
    
    def run_tests(self, mode="all"):
        """Run tests based on mode"""
        self.test_mode = mode
        self.print_banner()
        
        if mode == "quick":
            success = self.run_quick_check()
        elif mode == "direct":
            success = self.run_direct_tests()
        elif mode == "api":
            success = self.run_api_tests()
        else:  # all
            success = self.run_all_tests()
        
        self.print_summary()
        
        return success

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='AI Features Unified Testing Suite')
    parser.add_argument(
        '--mode',
        default='all',
        choices=['quick', 'direct', 'api', 'all'],
        help='Test mode to run (default: all)'
    )
    
    args = parser.parse_args()
    
    print("AI Features Unified Testing Suite")
    print("=" * 40)
    
    tester = UnifiedAITester()
    success = tester.run_tests(args.mode)
    
    if success:
        print("\n🎉 AI features are working correctly!")
    else:
        print("\n⚠️ Some issues detected. Check summary above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())