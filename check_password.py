#!/usr/bin/env python3
import os
import sys
import django
import bcrypt

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_passwords():
    """测试不同密码"""
    try:
        from stu_accounts.models import StudentAccount
        
        account = StudentAccount.objects.get(student_id="z1234567")
        print(f"账号: {account.student_id}")
        print(f"姓名: {account.name}")
        print(f"邮箱: {account.email}")
        
        # 测试常用密码
        test_passwords = [
            "password123",
            "Asdfgh123",
            "123456",
            "z1234567",
            "password",
        ]
        
        print("\n测试密码:")
        for pwd in test_passwords:
            try:
                ok = bcrypt.checkpw(pwd.encode("utf-8"), account.password_hash.encode("utf-8"))
                if ok:
                    print(f"✅ 密码正确: {pwd}")
                    return
            except:
                pass
        
        print("❌ 没有找到正确的密码")
        print(f"\n密码哈希: {account.password_hash[:30]}...")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_passwords()
