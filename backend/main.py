"""
FastAPI 应用入口

启动方式：
  1. python main.py
  2. uvicorn main:app --host 0.0.0.0 --port 3680

端口保护：自动检测并清理端口占用
"""
import os
import sys
import time
import socket
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.database import Base, engine
from app.api import auth, knowledge, documents, chat, logs

# 服务端口配置
SERVICE_PORT = 3680


def find_process_by_port(port: int) -> list:
    """查找占用指定端口的进程

    Args:
        port: 端口号

    Returns:
        占用端口的进程 PID 列表
    """
    pids = []
    try:
        if sys.platform == "win32":
            # Windows 系统
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.append(int(pid))
        else:
            # Linux/macOS 系统
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip().isdigit():
                    pids.append(int(line.strip()))
    except Exception as e:
        print(f"[端口保护] 查找进程失败: {e}")

    return list(set(pids))  # 去重


def kill_process_by_pid(pid: int) -> bool:
    """终止指定 PID 的进程

    Args:
        pid: 进程 ID

    Returns:
        是否成功终止
    """
    try:
        if sys.platform == "win32":
            # Windows 系统
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        else:
            # Linux/macOS 系统
            os.kill(pid, 9)
            return True
    except Exception as e:
        print(f"[端口保护] 终止进程 {pid} 失败: {e}")
        return False


def check_and_free_port(port: int) -> bool:
    """检查并释放被占用的端口

    Args:
        port: 目标端口号

    Returns:
        端口是否可用
    """
    print(f"[端口保护] 检查端口 {port} 是否被占用...")

    pids = find_process_by_port(port)

    if not pids:
        print(f"[端口保护] 端口 {port} 可用")
        return True

    print(f"[端口保护] 端口 {port} 被进程 {pids} 占用，正在清理...")

    success_count = 0
    for pid in pids:
        if kill_process_by_pid(pid):
            print(f"[端口保护] 成功终止进程 {pid}")
            success_count += 1
        else:
            print(f"[端口保护] 终止进程 {pid} 失败")

    if success_count > 0:
        time.sleep(1)  # 等待端口释放
        print(f"[端口保护] 已清理 {success_count} 个占用进程")
        return True

    return False


def is_port_available(port: int) -> bool:
    """检查端口是否可用

    Args:
        port: 端口号

    Returns:
        端口是否可用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # 返回 True 表示端口可用
    except Exception:
        return True


# 端口保护标志，防止重复执行
_port_check_done = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭事件"""
    global _port_check_done

    # 启动时执行端口检查（只执行一次）
    if not _port_check_done:
        print(f"\n{'='*60}")
        print(f"图书馆智能问答系统 - 后端服务")
        print(f"{'='*60}")
        print(f"[启动] 目标端口: {SERVICE_PORT}")

        if not is_port_available(SERVICE_PORT):
            print(f"[端口保护] 端口 {SERVICE_PORT} 被占用，正在清理...")
            check_and_free_port(SERVICE_PORT)
        else:
            print(f"[端口保护] 端口 {SERVICE_PORT} 可用")

        _port_check_done = True

    # 初始化数据库
    Base.metadata.create_all(bind=engine)
    print(f"[启动] 数据库初始化完成")

    yield

    # 关闭时执行清理
    print(f"[关闭] 服务正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    description="基于 RAG 的高校图书馆智能咨询助手",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(logs.router)


@app.get("/")
def root():
    return {"message": "Library AI Assistant API", "version": settings.APP_VERSION}


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "port": SERVICE_PORT}


if __name__ == "__main__":
    import uvicorn

    # 启动前检查并释放端口
    print(f"\n{'='*60}")
    print(f"图书馆智能问答系统 - 后端服务")
    print(f"{'='*60}")
    print(f"[启动] 目标端口: {SERVICE_PORT}")

    if not check_and_free_port(SERVICE_PORT):
        print(f"[错误] 无法释放端口 {SERVICE_PORT}，请手动处理")
        sys.exit(1)

    print(f"[启动] 正在启动服务...")
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
