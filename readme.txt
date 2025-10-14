10.14 update1
1.修改了home/profile界面的学号，邮箱显示
2.增加了路由保护功能，所有localstorage在登录后15分钟后清空token
3.待完成：
a.头像设置额；
b.登录的逻辑要改：用主键去查，也就是id而不是邮箱。后期前端修改：注册要名字，邮箱，id，密码；登录要id和密码，
c.b的基础上在home/profile上显示名字和邮箱
d.设置头像

10.14 update2
1.修改了登录逻辑
2.修改了注册要求
3.若干页面显示完成
4.头像设置完成
5.设置了学生账户某些属性非空
待完成:
编写其余接口
添加逻辑：邮件是否合理；id是否合理，用re；参数是否区分大小写？

10.14 update3
1.彻底删除了旧demo的参与内容包括course文件夹，以及废弃html网页文件
2.取消了常量token占位，创建了动态生成token和根据token提取id的函数，存放于后端的utils文件夹下。
f12访问结果如下：
{
    "success": true,
    "message": "OK",
    "data": {
        "token": "eyJzdHVkZW50X2lkIjogIno1NTQwNzMwIn0=",
        "user": {
            "studentId": "z5540730",
            "name": "Winn",
            "email": "whitemingcyj@outlook.com",
            "avatarUrl": "/media/z5540730/z5540730_ZHe9b9A0.png"
        }
    }
}
3.完成了preference的接口，preference已经可以存入数据库
4.对于preference，数据库中有两张表，分别代表当前pre和default pre，主键是id；
5.移除了数据库中material和course表
6.生成plan可以直接通过apply里的toSave(json)文件用作参数传给ai，可以选择忽略description；
7.reschedule的时候可以先通过token获取student+_id 然后访问数据库取数据(sprint2)
待完成:
1.token持久化以及JWT的应用
2.添加逻辑：邮件是否合理；id是否合理，用re；参数是否区分大小写？
3.所有页面的路由保护(已完成home和profile)
4.course部分和plan部分请创建文件夹在django_backend下

10.15:
1.course部分已经完成
2.对于对接生成计划： generate 中的apply 按钮点下 会触发 preferenceStore.ts里258行的方法，我分别在268，273,297列出了
pre，course，task的信息；可以在网页上f12 打开控制台查看
要注意：最初前端捏的数据中task有5个属性值，所以数据库中有5个属性值。并且coursesStore.getCourseTasks(course.id) 
只能获取一门课的task
所以：想要对齐text_run.py里的结构 我的建议是：用循环遍历当前student_id下所有course_id，对于每一个course_id执行
getCourseTasks,并用map筛选出你要的4个属性，我看了下应该是不要percentcontribution，然后放进数组。
url就是pdf的路径，我已经存放好了，也写入数据库了，就在后端的task文件夹下，和原本的内容一样只不过改了个名字

