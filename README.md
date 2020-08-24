## 简介
“表情宝”后端。

功能：
- 图片浏览、分享。
- 添加、删除图片。
- 给图片打标签，并可以按标签搜索。
- 图片分组。
- 图片导入导出。

## 自动部署：
```
$ python setup.py sdist
$ cd deploy
$ pyinfra -v inventory.py update.py
```

## 手动部署：
依赖：
- postgresql

```bash
$ python3 setup.py sdist
$ scp dist/biaoqingbao-x.x.x.tar.gz <user>@<host>:/opt/www/biaoqingbao
$ scp env.sh.example <user>@<host>:/opt/www/biaoqingbao/env.sh

$ ssh <user>@<host>
$ cd /opt/www/biaoqingbao
$ python3 -m venv .venv
$ . .venv/bin/activate
$ pip install biaoqingbao-x.x.x.tar.gz

$ vi env.sh # 填写好程序运行所需环境变量。
$ source env.sh

$ biaoqingbao create-table
$ biaoqingbao run
```

## 开发：
说明：
后端使用 Python Flask + waitress，前端使用 React + material-ui 开发。

后端：
```bash
$ git clone https://github.com/valleygtc/biaoqingbao.git
$ cd biaoqingbao

# create venv
$ python3 -m venv .venv
$ source .venv/bin/activate
# install biaoqingbao and its dependencies.
$ pip install --editable .[dev]

# ENV
$ cp env.sh.example env.sh
$ vi env.sh # 填写好程序运行所需环境变量。
$ source env.sh # 读入环境变量。

# run unittest discover
$ python -m unittest

$ biaoqingbao create-table
$ flask run
```

前端：

见：https://github.com/valleygtc/biaoqingbao-frontend

## 构建与发布：
TODO：docker
