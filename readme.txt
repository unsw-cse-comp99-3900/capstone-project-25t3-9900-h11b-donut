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
