# TODO
# 接口规定：
前后端通信使用 HTTP 协议，操作（请求）的成功失败使用 HTTP 状态码来表示，body 均为 JSON 格式。

成功返回的数据放在 "data" 字段，如果是成功消息则放在 "msg" 字段，异常消息放在 "error" 字段。

成功返回数据示例：
```json
GET /events/
resp: 200, body:
{
    "data": [
        {
            "id": 1,
            "name": "xxx",
            "remark": "xxx",
            "create_at": "xxxx"
        },
        ...
    ]
}
```

成功返回消息示例：
```json
POST /events/add
resp: 200, body:
{
    "msg": "成功添加event: xxxxxxxxxxx"
}
```

发生异常示例：
```json
GET /events/delete?id=10000
resp: 404, body:
{
    "error": "无event(id=10000)，可能是其已被删除，请刷新页面。"
}
```

- 各个接口具体格式见view.py中的每个**视图函数上方的注释**。


# 状态码规定
- 200 OK
- 400 Bad Request: 服务器不理解客户端的请求，未做任何处理。（eg. 前端传来的数据格式错误。）
- 401 Unauthorized: 用户未登录
- 403 Forbidden: 登陆的用户没有此操作权限
- 404 NOT FOUND: 用户发出的请求针对的是不存在的记录，服务器没有进行操作，该操作是幂等的。（eg. 要删除不存在的项）
- 500 Internal Server Error: 数据库蹦了，cmdb 接口异常，及其他未捕获异常
- Flask 框架自行处理的异常情况，如：404 Not Found 等


# 其他规定
- 时间字符串格式规定：datetime -> "YYYY-mm-dd HH:MM:SS", eg: "2019-02-19 17:00:00"。


# 异常情况说明
用户未登录：
```
resp: 401 Unauthorized, body:
{
    "error": "用户未登录",
}
```


登陆的用户没有此操作权限：
```
resp: 403 Forbidden, body:
{
    "error": "已登录的用户没有使用该 app 的权限，如需使用，请联系管理员。"
}
```
