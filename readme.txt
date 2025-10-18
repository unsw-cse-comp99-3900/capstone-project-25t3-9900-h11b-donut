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
2.右上角显示ddl完成部分；(注意！数据库中ddl的参数要详细到小时和分钟，因为api.ts里计算时间差细化到了分钟！)
3.对于对接生成计划： generate 中的apply 按钮点下 会触发 preferenceStore.ts里258行的方法，我分别在268，273,297列出了
pre，course，task的信息；可以在网页上f12 打开控制台查看
要注意：最初前端捏的数据中task有5个属性值，所以数据库中有5个属性值。并且coursesStore.getCourseTasks(course.id) 
只能获取一门课的task
所以：想要对齐text_run.py里的结构 我的建议是：用循环遍历当前student_id下所有course_id，取student_id可以用session取
或者django/utils/auth.py里的函数，course/views.py中的_require_student或许可以给启示
对于每一个course_id执行
getCourseTasks,并用map筛选出你要的4个属性，我看了下应该是不要percentcontribution，然后放进数组。
url就是pdf的路径，我已经存放好了，也写入数据库了，就在后端的task文件夹下，和原本的内容一样只不过改了个名字

10.16:
1.完成了plan部分
发现问题：
1.目前plan是存放在local storage的不是数据库，所以：我在我的电脑上登我的号能看到plan，其余人不一定
2.切换用户的时候存在一个大问题：会显示之前一个用户的数据，比如 课程，ddl.必须刷新才会回归正常。
目前我做到了：可以让localStorage的内容立马取出，也就是说，切换用户，只要localStorage有东西，就会立马显示，比如plan
但是database还没解决。 
3. 刷新后没显示课程plan，和登录进去一样，需要等database响应。现在刷新登录后都会很快看到plan。
4. 每周学一天每天学1小时的问题


所以待解决的：
1.我会继续解决这个问题：刷新后课程突然没有，要点两下才会出现；切换账号后显示前一个账号的问题；
2.我会完善路由保护机制，避免出现输出9900donut:5317/#/plan直接就进网站了。以及token持久化，保证一个账号只能在一个地方登录
3.我会修改task表的ddl格式，精确到时间，并检测新格式会不会对ai生成plan有影响.

个人建议：
1.后端同学完成进度展示部分
2.前端同学辛苦一下周末把Admin端和选择课程页面做好，如果有上传资料的按钮这种更好。只做这么多
我想象的界面：My course：选择课程，加入，然后点击课程会显示所有task以及material,然后可以选择上传task或者material
然后manage My course： 会显示自己管理的课程，点击去后会显示所有这门课学生的进度情况

3.第六周我会完成Admin的登录注册，选课，上传task，material。以及学生端的消息提示
4.希望有同学能检查目前为止的代码，进行整理，比如删除废弃函数这种

10.18：
update1:
1.修复了切换账号带来的显示bug
2.缺陷：刷新后要等2秒左右才会显示课程，因为要等请求传递再从数据库中取

update2:
1.修复了缺陷：将课程信息（包括ddl）存入localStorage,可以进入网页f12看（详情可见courseStore）
2.完善了token持久化，仅一人可登录账号，在所有功能中添加token对比代码

update3:
1.使用随机生成token,并修改了与之相关的函数，保证能正确根据token从数据库中读取学生id
2.改进了token持久化的逻辑，原方法代码修改量太大,注意，异地登录的测试只能在服务器上测试，本地测试会因为localStorage的缘故导致新网页也会登出！
（注意必须做出请求的时候才会提示登出，比如添加课程删除课程，不涉及request的操作不会登出！）
3.增添了邮箱格式的验证功能（只是格式，不管是否存在），以及人名密码学号的合理性判断
4.完成了路由保护,替换了原来的方法，选择在App.tsx里修改，后续待保护的路由可以在里面加
5.修改了读取preference的逻辑：只有登录进去后才会根据student_id从local storage中取出plan

