

### 编辑器

PyCharm  

### 前端技术

基础：Html+Css+JavaScript

框架：[BootStrap](https://www.bootcss.com/)+[JQuery](https://jquery.com/)

### 后端技术

Django

数据库：MySQL

## 本地运行

1.下载zip直接解压
2.使用 Pycharm 打开项目，配置python编译环境，
3.打开Navicat For Mysql，创建booksdb数据库
4.使用命令启动 Django 项目 `python manage.py runserver`
5.通过浏览器访问系统主页面（包括后台）

* 前台首页：`http://127.0.0.1:8000/`
* 后台首页：`http://127.0.0.1:8000/admin`

## 注意
* 注意 Django 项目启动应该先切入`cd manage.py所在目录`。
* 注意**修改setting.py**中数据库相关的内容。
* 系统中不存在后台管理员账号，可以**使用命令`python manage.py createsuperuser`创建**即可。
