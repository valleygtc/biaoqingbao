# 简介
“表情宝”后端。

功能：
- 图片浏览、分享。
- 添加、删除图片。
- 给图片打标签，并可以按标签搜索。
- 图片分组。
- 图片导入导出。

# 安装：
TODO：docker

# 使用：
TODO：docker

# 开发：
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

# run unittest discover
$ python -m unittest

# ENV
$ cp env.sh.example env.sh
$ vi env.sh # 填写好程序运行所需环境变量。
$ source env.sh # 读入环境变量。

$ flask run
```

前端：

见：https://github.com/valleygtc/biaoqingbao-frontend

# 构建与发布：
TODO：docker
