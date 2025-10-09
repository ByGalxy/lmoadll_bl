"""
-*- coding: utf-8 -*-
Gunicorn配置文件
"""
import multiprocessing



# 绑定地址和端口
bind = "0.0.0.0:2324"
# 工作进程类型，可以是sync, gevent, eventlet等
worker_class = "sync"
# 进程ID文件
pidfile = "gunicorn.pid"
# 进程名称
proc_name = "lmoadll_bl"

# 每个工作进程的线程数
threads = 2
# 最大并发数
worker_connections = 512
# 请求超时时间(秒)
timeout = 30
# 保持活动连接的时间(秒)
keepalive = 2

daemon = False  # 守护进程模式(后台运行)
exit_on_timeout = True  # 最大请求数，超过后自动重启工作进程
reload = False  # 当代码有修改时自动重启
syslog = False  # 服务器标识
preload_app = True  # 预加载应用，减少内存使用和启动时间

# 工作进程数量，通常设置为CPU核心数的2倍加1
workers = multiprocessing.cpu_count() * 2 + 1

# 访问日志格式
accesslog = "-"  # 输出到标准输出
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 错误日志格式
errorlog = "-"  # 输出到标准错误
loglevel = "info"

# 环境变量
env = {"PRODUCTION": "True"}

"""
代理配置 - 信任所有代理IP
在经过接受数据的时候, 通常有一个反向代理服务器(如Nginx)在前端. 这些代理服务器会将客户端的真实IP地址放在请求头中, 
如X-Forwarded-For. Gunicorn默认不信任这些头部信息, 因为它们可能被伪造. 通过设置forwarded_allow_ips, 可以指定哪些代理IP是可信的. 
"""
forwarded_allow_ips = "*"  # *或者指定具体的代理IP，如 '127.0.0.1,10.0.0.1'

# 安全头部配置
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
