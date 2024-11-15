import subprocess
import sys
import os
import time
import webbrowser
import signal
import platform
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, runner):
        self.runner = runner
        
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"\n📝 检测到后端文件变更: {event.src_path}")
            self.runner.reload_backend()
        elif event.src_path.endswith(('.vue', '.js', '.ts')):
            print(f"\n📝 检测到前端文件变更: {event.src_path}")
            # 前端有自己的热重载机制，不需要我们处理

class ProjectRunner:
    def __init__(self):
        self.frontend_process = None
        self.backend_process = None
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.host_ip = "10.6.16.151"
        self.frontend_port = "8081"
        self.backend_port = "5000"
        self.observer = Observer()
        
    def reload_backend(self):
        """重新加载后端服务"""
        print("🔄 重新加载后端服务...")
        if self.backend_process:
            # 终止旧进程及其子进程
            parent = psutil.Process(self.backend_process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            
        # 启动新的后端进程
        self.start_backend()
        print("✅ 后端服务已重新加载")
        
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务器...")
        backend_dir = os.path.join(self.project_root, 'oneAI')
        
        try:
            import uvicorn
            import fastapi
            print("✅ 已安装必要的包: uvicorn, fastapi")
        except ImportError:
            print("📦 安装后端依赖...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'uvicorn', 'fastapi', 'watchdog', 'psutil'], check=True)
        
        # 使用uvicorn的reload模式
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.backend_process = subprocess.Popen(
                [
                    sys.executable, 
                    '-m', 'uvicorn', 
                    'app:app',
                    '--host', self.host_ip,
                    '--port', self.backend_port,
                    '--reload'
                ],
                cwd=backend_dir,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                startupinfo=startupinfo
            )
        else:
            self.backend_process = subprocess.Popen(
                [
                    sys.executable, 
                    '-m', 'uvicorn', 
                    'app:app',
                    '--host', self.host_ip,
                    '--port', self.backend_port,
                    '--reload'
                ],
                cwd=backend_dir,
                env=os.environ.copy(),
                preexec_fn=os.setsid
            )

    def start_frontend(self):
        """启动前端服务"""
        print("🚀 启动前端服务器...")
        frontend_dir = os.path.join(self.project_root, 'frontend')
        
        if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
            print("📦 安装前端依赖...")
            subprocess.run('npm install', shell=True, cwd=frontend_dir, check=True)
        
        env = os.environ.copy()
        env['PORT'] = self.frontend_port
        env['HOST'] = self.host_ip
        
        self.frontend_process = subprocess.Popen(
            'npm run serve',
            shell=True,
            cwd=frontend_dir,
            env=env
        )

    def setup_file_watchers(self):
        """设置文件监视器"""
        backend_dir = os.path.join(self.project_root, 'oneAI')
        frontend_dir = os.path.join(self.project_root, 'frontend', 'src')
        
        handler = CodeChangeHandler(self)
        self.observer.schedule(handler, backend_dir, recursive=True)
        self.observer.schedule(handler, frontend_dir, recursive=True)
        self.observer.start()

    def cleanup(self, signum=None, frame=None):
        """清理进程"""
        print("\n🛑 正在关闭服务...")
        
        # 停止文件监视
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        
        # 终止进程函数
        def terminate_process(process, name):
            if process and process.poll() is None:
                try:
                    if platform.system() == 'Windows':
                        parent = psutil.Process(process.pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.terminate()
                        parent.terminate()
                    else:
                        process.terminate()
                        process.wait(timeout=5)
                except Exception as e:
                    print(f"关闭{name}服务时出错: {e}")

        terminate_process(self.frontend_process, "前端")
        terminate_process(self.backend_process, "后端")
        
        print("✅ 服务已关闭")
        sys.exit(0)

    def run(self):
        """运行项目"""
        try:
            print("🚀 启动项目服务...")
            print(f"项目根目录: {self.project_root}")
            
            # 检查必要的目录
            if not os.path.exists(os.path.join(self.project_root, 'oneAI')):
                raise Exception("找不到后端目录 'oneAI'")
            if not os.path.exists(os.path.join(self.project_root, 'frontend')):
                raise Exception("找不到前端目录 'frontend'")
            
            # 启动服务
            self.start_backend()
            self.start_frontend()
            
            # 设置文件监视器
            self.setup_file_watchers()
            
            # 注册信号处理
            signal.signal(signal.SIGINT, self.cleanup)
            signal.signal(signal.SIGTERM, self.cleanup)
            
            print("\n✨ 服务已启动!")
            print(f"- 前端地址: http://{self.host_ip}:{self.frontend_port}")
            print(f"- 后端地址: http://{self.host_ip}:{self.backend_port}")
            print("\n👀 正在监视文件变更...")
            print("按 Ctrl+C 可停止服务...")
            
            # 保持程序运行
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")
            self.cleanup()

if __name__ == "__main__":
    runner = ProjectRunner()
    runner.run()