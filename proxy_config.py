#!/usr/bin/env python3
"""
代理配置管理器
用于配置和管理网络代理设置
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class ProxyManager:
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.http_port = "7890"
        self.socks_port = "7890"
        
        # 代理配置
        self.http_proxy = f"http://{self.proxy_host}:{self.http_port}"
        self.https_proxy = f"http://{self.proxy_host}:{self.http_port}"
        self.socks_proxy = f"socks5://{self.proxy_host}:{self.socks_port}"
        
        # 检测操作系统和shell
        self.system = platform.system()
        self.shell = self.detect_shell()
        self.config_file = self.get_config_file()
    
    def detect_shell(self):
        """检测当前使用的shell"""
        shell_path = os.environ.get('SHELL', '/bin/bash')
        return os.path.basename(shell_path)
    
    def get_config_file(self):
        """获取对应shell的配置文件路径"""
        home = Path.home()
        if self.shell == 'zsh':
            return home / '.zshrc'
        elif self.shell == 'bash':
            if self.system == 'Darwin':  # macOS
                return home / '.bash_profile'
            else:  # Linux
                return home / '.bashrc'
        else:
            return home / '.profile'
    
    def set_environment_proxy(self):
        """设置当前会话的环境变量"""
        print("🔧 设置当前会话代理环境变量...")
        
        os.environ['http_proxy'] = self.http_proxy
        os.environ['https_proxy'] = self.https_proxy
        os.environ['all_proxy'] = self.socks_proxy
        os.environ['HTTP_PROXY'] = self.http_proxy
        os.environ['HTTPS_PROXY'] = self.https_proxy
        os.environ['ALL_PROXY'] = self.socks_proxy
        
        # npm 代理设置
        os.environ['npm_config_proxy'] = self.http_proxy
        os.environ['npm_config_https_proxy'] = self.https_proxy
        
        print("✅ 当前会话代理已设置")
        self.show_proxy_status()
    
    def unset_environment_proxy(self):
        """取消当前会话的代理设置"""
        print("🔧 取消当前会话代理设置...")
        
        proxy_vars = [
            'http_proxy', 'https_proxy', 'all_proxy',
            'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
            'npm_config_proxy', 'npm_config_https_proxy'
        ]
        
        for var in proxy_vars:
            os.environ.pop(var, None)
        
        print("✅ 当前会话代理已取消")
    
    def add_to_shell_config(self):
        """将代理配置添加到shell配置文件"""
        print(f"🔧 添加代理配置到 {self.config_file}...")
        
        proxy_config = f"""
# 代理设置 (由 proxy_config.py 添加)
export http_proxy={self.http_proxy}
export https_proxy={self.https_proxy}
export all_proxy={self.socks_proxy}
export HTTP_PROXY={self.http_proxy}
export HTTPS_PROXY={self.https_proxy}
export ALL_PROXY={self.socks_proxy}

# npm 代理设置
export npm_config_proxy={self.http_proxy}
export npm_config_https_proxy={self.https_proxy}

# 修复 npm 全局包 PATH
export PATH="$(npm config get prefix)/bin:$PATH"
"""
        
        # 检查是否已经存在配置
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                content = f.read()
                if 'proxy_config.py' in content:
                    print("⚠️  配置文件中已存在代理设置")
                    return
        
        # 添加配置
        with open(self.config_file, 'a') as f:
            f.write(proxy_config)
        
        print(f"✅ 代理配置已添加到 {self.config_file}")
        print(f"💡 请运行以下命令重新加载配置:")
        print(f"   source {self.config_file}")
    
    def remove_from_shell_config(self):
        """从shell配置文件中移除代理配置"""
        print(f"🔧 从 {self.config_file} 移除代理配置...")
        
        if not self.config_file.exists():
            print("⚠️  配置文件不存在")
            return
        
        with open(self.config_file, 'r') as f:
            lines = f.readlines()
        
        # 过滤掉代理配置相关的行
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if 'proxy_config.py' in line:
                skip_section = True
                continue
            elif skip_section and line.strip() == '':
                skip_section = False
                continue
            elif not skip_section:
                filtered_lines.append(line)
        
        with open(self.config_file, 'w') as f:
            f.writelines(filtered_lines)
        
        print(f"✅ 代理配置已从 {self.config_file} 移除")
    
    def show_proxy_status(self):
        """显示当前代理状态"""
        print("\n📊 当前代理状态:")
        print(f"   http_proxy:  {os.environ.get('http_proxy', '未设置')}")
        print(f"   https_proxy: {os.environ.get('https_proxy', '未设置')}")
        print(f"   all_proxy:   {os.environ.get('all_proxy', '未设置')}")
        print()
    
    def test_proxy_connection(self):
        """测试代理连接"""
        print("🔍 测试代理连接...")
        
        try:
            import requests
            
            # 设置代理
            proxies = {
                'http': self.http_proxy,
                'https': self.https_proxy
            }
            
            # 测试连接
            response = requests.get('https://httpbin.org/ip', 
                                  proxies=proxies, 
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 代理连接成功!")
                print(f"   当前IP: {data.get('origin', 'unknown')}")
            else:
                print(f"❌ 代理连接失败: HTTP {response.status_code}")
                
        except ImportError:
            print("⚠️  需要安装 requests 库进行连接测试")
            print("   pip install requests")
        except Exception as e:
            print(f"❌ 代理连接失败: {e}")
    
    def configure_git_proxy(self):
        """配置Git代理"""
        print("🔧 配置Git代理...")
        
        try:
            subprocess.run(['git', 'config', '--global', 'http.proxy', self.http_proxy])
            subprocess.run(['git', 'config', '--global', 'https.proxy', self.https_proxy])
            print("✅ Git代理配置成功")
        except Exception as e:
            print(f"❌ Git代理配置失败: {e}")
    
    def remove_git_proxy(self):
        """移除Git代理配置"""
        print("🔧 移除Git代理配置...")
        
        try:
            subprocess.run(['git', 'config', '--global', '--unset', 'http.proxy'])
            subprocess.run(['git', 'config', '--global', '--unset', 'https.proxy'])
            print("✅ Git代理配置已移除")
        except Exception as e:
            print(f"❌ Git代理配置移除失败: {e}")
    
    def show_menu(self):
        """显示菜单"""
        print("\n" + "="*50)
        print("🚀 代理配置管理器")
        print("="*50)
        print("1. 设置当前会话代理")
        print("2. 取消当前会话代理")
        print("3. 添加代理到shell配置文件")
        print("4. 从shell配置文件移除代理")
        print("5. 显示代理状态")
        print("6. 测试代理连接")
        print("7. 配置Git代理")
        print("8. 移除Git代理")
        print("9. 退出")
        print("="*50)
    
    def run(self):
        """运行主程序"""
        while True:
            self.show_menu()
            choice = input("请选择操作 (1-9): ").strip()
            
            if choice == '1':
                self.set_environment_proxy()
            elif choice == '2':
                self.unset_environment_proxy()
            elif choice == '3':
                self.add_to_shell_config()
            elif choice == '4':
                self.remove_from_shell_config()
            elif choice == '5':
                self.show_proxy_status()
            elif choice == '6':
                self.test_proxy_connection()
            elif choice == '7':
                self.configure_git_proxy()
            elif choice == '8':
                self.remove_git_proxy()
            elif choice == '9':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择，请重试")
            
            input("\n按回车键继续...")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式
        proxy_manager = ProxyManager()
        command = sys.argv[1].lower()
        
        if command == 'on':
            proxy_manager.set_environment_proxy()
        elif command == 'off':
            proxy_manager.unset_environment_proxy()
        elif command == 'status':
            proxy_manager.show_proxy_status()
        elif command == 'test':
            proxy_manager.test_proxy_connection()
        elif command == 'install':
            proxy_manager.add_to_shell_config()
        elif command == 'uninstall':
            proxy_manager.remove_from_shell_config()
        else:
            print("用法:")
            print("  python proxy_config.py on       # 开启代理")
            print("  python proxy_config.py off      # 关闭代理")
            print("  python proxy_config.py status   # 查看状态")
            print("  python proxy_config.py test     # 测试连接")
            print("  python proxy_config.py install  # 安装到shell配置")
            print("  python proxy_config.py uninstall # 从shell配置移除")
    else:
        # 交互模式
        proxy_manager = ProxyManager()
        proxy_manager.run()

if __name__ == "__main__":
    main()