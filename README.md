# 表情宝

在线地址：[bqb.plus](https://bqb.plus)

功能：
- 图片浏览、分享。
- 添加、删除图片。
- 给图片打标签，并可以按标签搜索。
- 图片分组。
- 图片导入导出。

## 应用截图：

<div align="center">
    <img src="./assets/compose.png" alt="应用截图">
</div>

## 部署：

### 依赖：

- postgresql

### 手动部署：

```bash
$ git clone https://github.com/valleygtc/biaoqingbao.git
$ cd biaoqingbao
$ python3 -m venv .venv
$ . .venv/bin/activate
$ poetry install --with prod

$ vi env.sh # 填写好程序运行所需环境变量。
$ source env.sh

$ biaoqingbao create-table
$ biaoqingbao run
```

### 自动更新：

```
$ python setup.py sdist
$ cd deploy
$ pyinfra -v inventory.py update.py
```

## 开发：

后端：
```bash
$ git clone https://github.com/valleygtc/biaoqingbao.git
$ cd biaoqingbao

# create venv
$ python3 -m venv .venv
$ source .venv/bin/activate
# install biaoqingbao and its dependencies.
$ poetry install --with=dev

# ENV
$ cp env.dev.sh.example env.sh
$ vi env.sh # 填写好程序运行所需环境变量。
$ source env.sh # 读入环境变量。

$ pytest
$ biaoqingbao create-table
$ flask run
```

前端代码仓库：[biaoqingbao-frontend](https://github.com/valleygtc/biaoqingbao-frontend)
