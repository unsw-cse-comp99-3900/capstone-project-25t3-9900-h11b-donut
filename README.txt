1.避免安装mysql
2.vscode里跑不了，因为用的是容器里的数据库，如果想本地跑，手动修改app.py头部的数据库参数
3.启动docker desktop,vscode中输入docker compose up --build创建镜像和container就可以在ontainer里跑
4.容器是隔离的所以不用担心不断录入数据影响其他成员的存量；清除数据方式可百度
5.check 容器里的数据库的方法：
win+r启动cmd，输入docker exec -it capstone-project-25t3-9900-h11b-donut-db-1 bash
然后输入mysql -u root -p登录
密码我设置为：root(见.env)
6. show databases; 查看数据库，应该是ai_learning_coach这个数据库
7. use ai_learning_coach 进入数据库
8. show tables;可以看表
9. select * from ..... 选择表名可以看表的数据
10.\q退出
11. .env.example这个文件可以不用管
12. 因为是测试版，所以不gitignore .env

10.11 update:
放弃了docker内部的数据库，使用TiDB云端数据库，放开了IP地址范围。
同样不需要本地配置Mysql环境，直接链接云端数据库，用TiDB自带的终端便可以查看存入的数据
新增了上传pdf文件并下载pdf的文件，由于都是在学生端发生的，所以后期需要改成管理员端
修改包括table和相对应的页面，以及逻辑
10.12 update:
上传文件可能存在问题，目前考虑方案：统一上传到云端服务器

