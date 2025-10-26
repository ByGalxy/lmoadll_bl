# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0


import os
import sys
import argparse
import subprocess
from gunicorn_config import bind



def main():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动Gunicorn服务器")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    port_from_config = int(bind.split(':')[-1])
    parser.add_argument("--port", type=int, default=port_from_config, help="服务器端口号")
    parser.add_argument("--workers", type=int, default=None, help="工作进程数量")
    parser.add_argument(
        "--env",
        type=str,
        default="production",
        choices=["development", "production"],
        help="运行环境",
    )
    args = parser.parse_args()

    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    # 构建gunicorn命令
    cmd = [
        "gunicorn",
        "lmoadll_bl:app",
        "--config",
        "gunicorn_config.py",
    ]

    # 根据参数调整命令
    if args.daemon:
        cmd.append("--daemon")

    if args.port != port_from_config:
        cmd.extend(["--bind", f"127.0.0.1:{args.port}"])

    if args.workers is not None:
        cmd.extend(["--workers", str(args.workers)])

    if args.env == "development":
        cmd.extend(["--reload"])
        print("\n⚠️ 开发模式: 代码变更时会自动重启服务器\n")
    else:
        print("\n🚀 生产模式：使用多进程提高性能\n")

    # 显示启动信息
    print("正在启动Gunicorn服务器...")
    print("-" * 42)
    print(f"命令: {' '.join(cmd)}")
    print(f"配置端口: {port_from_config}")
    print(f"运行端口: {args.port}")

    # 检查是否安装了gunicorn
    try:
        subprocess.run(
            ["gunicorn", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError:
        print("\n❌ 错误喵: 未安装gunicorn或不支持您当前平台")
        print("请先运行: pip install -r requirements.txt")
        sys.exit(1)

    # 启动gunicorn
    try:
        print("\n服务器启动中...")

        # 使用Popen启动并添加进程记录
        process = subprocess.Popen(cmd)
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            print("\n服务器已停止喵")
            
    except KeyboardInterrupt:
        print("\n服务器已停止喵")
    except Exception as e:
        print(f"\n❌ 启动失败喵: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
