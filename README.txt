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
