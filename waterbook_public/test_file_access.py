#!/usr/bin/env python3
"""
测试文件访问功能
检查修复后的server.py是否能正确提供meta.json和loop.mp4文件
"""

import requests
import time

def test_file_access():
    """测试文件访问功能"""
    base_url = "http://127.0.0.1:8000"
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 测试文件列表
    test_files = [
        "/cover.png",
        "/loop.mp4", 
        "/meta.json",
        "/api/status"
    ]
    
    print(f"测试服务器: {base_url}")
    print("=" * 50)
    
    for file_path in test_files:
        try:
            url = base_url + file_path
            response = requests.get(url, timeout=5)
            
            print(f"文件: {file_path}")
            print(f"状态码: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"内容长度: {content_length} bytes")
                
                # 如果是JSON文件，显示部分内容
                if file_path.endswith('.json'):
                    try:
                        json_data = response.json()
                        print(f"JSON内容预览: {str(json_data)[:200]}...")
                    except:
                        print("JSON解析失败")
                        
                print("✅ 访问成功")
            else:
                print(f"❌ 访问失败: {response.status_code}")
                if response.text:
                    print(f"错误信息: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            
        print("-" * 30)

if __name__ == "__main__":
    test_file_access()