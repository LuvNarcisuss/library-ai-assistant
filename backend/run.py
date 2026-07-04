"""
图书馆智能问答系统 - 启动脚本

使用方式：
  python run.py
  python run.py --port 8000
  python run.py --host 0.0.0.0 --port 3680

功能：
  - 自动检测并清理端口占用
  - 启动 FastAPI 服务
"""
import os
import sys
import argparse
import uvicorn

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import SERVICE_PORT, check_and_free_port


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="图书馆智能问答系统 - 启动脚本")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=SERVICE_PORT, help=f"监听端口 (默认: {SERVICE_PORT})")
    parser.add_argument("--reload", action="store_true", help="启用热重载")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"图书馆智能问答系统 - 后端服务")
    print(f"{'='*60}")
    print(f"[配置] 监听地址: {args.host}")
    print(f"[配置] 监听端口: {args.port}")
    print(f"[配置] 热重载: {'启用' if args.reload else '禁用'}")
    print(f"{'='*60}\n")

    # 检查并释放端口
    print(f"[启动] 正在检查端口 {args.port}...")
    if not check_and_free_port(args.port):
        print(f"[错误] 无法释放端口 {args.port}，请手动处理")
        print(f"[提示] 使用以下命令查找占用端口的进程:")
        print(f"       netstat -ano | findstr :{args.port}")
        sys.exit(1)

    print(f"[启动] 正在启动服务...")
    print(f"[启动] 服务地址: http://{args.host}:{args.port}")
    print(f"[启动] API 文档: http://localhost:{args.port}/docs")
    print(f"{'='*60}\n")

    # 启动服务
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
