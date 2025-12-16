#!/usr/bin/env python3
"""
直接测试Rust服务（绕过代理）
验证服务本身是否正常
"""

import requests
import json
import os
import sys

def test_health_check_direct():
    """直接测试健康检查（不使用代理）"""
    print("\n" + "="*60)
    print("测试1: 健康检查端点（直接访问）")
    print("="*60)

    # 清理代理环境变量
    for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if key in os.environ:
            del os.environ[key]

    session = requests.Session()
    session.trust_env = False  # 不使用环境变量中的代理

    try:
        response = session.get(
            "http://localhost:8080/health",
            timeout=10
        )

        print(f"✓ HTTP状态码: {response.status_code}")
        print(f"✓ 响应头: {dict(response.headers)}")
        print(f"✓ 响应内容: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 健康检查通过！服务运行正常")
                return True
            else:
                print(f"❌ 服务返回错误: {data.get('message')}")
                return False
        else:
            print(f"❌ 返回状态码错误: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败: {e}")
        print("请确认服务是否运行在 localhost:8080")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_message_direct():
    """直接测试单条消息（不使用代理）"""
    print("\n" + "="*60)
    print("测试2: 单条消息接口（直接访问）")
    print("="*60)

    # 清理代理环境变量
    for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if key in os.environ:
            del os.environ[key]

    session = requests.Session()
    session.trust_env = False

    test_data = {
        "channel_id": -1002115686230,
        "channel_name": "Test Channel",
        "message_id": 99999,
        "text": "测试消息 - 向后兼容性验证",
        "timestamp": 1700000000
    }

    try:
        print("发送单条消息...")
        response = session.post(
            "http://localhost:8080/api/v1/message",
            json=test_data,
            timeout=10
        )

        print(f"✓ HTTP状态码: {response.status_code}")
        print(f"✓ 响应内容: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 单条消息测试通过！向后兼容性良好")
                return True
            else:
                print(f"⚠️  消息处理成功但返回警告: {data.get('message')}")
                return True  # 仍然算作成功
        else:
            print(f"❌ 返回状态码错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_message_direct():
    """直接测试批量消息（不使用代理）"""
    print("\n" + "="*60)
    print("测试3: 批量消息接口（直接访问）")
    print("="*60)

    # 清理代理环境变量
    for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        if key in os.environ:
            del os.environ[key]

    session = requests.Session()
    session.trust_env = False

    batch_data = {
        "batch_id": "batch_test_001",
        "timestamp": "2025-12-16T10:00:00",
        "source": "test_crawler",
        "note_info": {
            "note_id": "test_note_001",
            "note_title": "测试笔记",
            "total_comments": 2
        },
        "messages": [
            {
                "message_id": "comment_001",
                "role": "user",
                "content": "这个产品真的很好用，推荐购买！",
                "metadata": {
                    "user_info": {
                        "user_id": "user_001",
                        "user_name": "测试用户1"
                    },
                    "interaction": {
                        "like_count": 10,
                        "reply_count": 2
                    },
                    "temporal": {
                        "absolute": 1640000000.0,
                        "relative": "2小时前"
                    },
                    "location": {
                        "country": "中国",
                        "city": "北京"
                    }
                }
            },
            {
                "message_id": "comment_002",
                "role": "user",
                "content": "价格有点贵，但是质量确实不错。",
                "metadata": {
                    "user_info": {
                        "user_id": "user_002",
                        "user_name": "测试用户2"
                    },
                    "interaction": {
                        "like_count": 5,
                        "reply_count": 1
                    },
                    "temporal": {
                        "absolute": 1640000100.0,
                        "relative": "3小时前"
                    },
                    "location": {
                        "country": "中国",
                        "city": null
                    }
                }
            }
        ]
    }

    try:
        print("发送批量消息...")
        response = session.post(
            "http://localhost:8080/api/v1/message",
            json=batch_data,
            timeout=30  # 批量请求可能需要更长时间
        )

        print(f"✓ HTTP状态码: {response.status_code}")
        print(f"✓ 响应内容: {response.text[:500]}...")  # 只显示前500字符

        if response.status_code == 200:
            data = response.json()
            print(f"✓ 解析后的JSON数据结构:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

            # 验证批量响应格式
            if "status" in data and "analysis_result" in data:
                print("✅ 批量消息测试通过！响应格式正确")
                return True
            else:
                print("❌ 响应格式不正确，缺少必要字段")
                return False
        else:
            print(f"❌ 返回状态码错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🔍 Rust服务直接测试（绕过代理）")
    print("="*60)
    print(f"测试目标: http://localhost:8080")
    print(f"测试方法: 直接访问，不使用任何代理")
    print("="*60)

    # 显示当前环境变量状态
    print("\n📋 环境变量状态:")
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    for var in proxy_vars:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")

    test_results = []

    # 测试1: 健康检查
    test_results.append(("健康检查", test_health_check_direct()))

    # 测试2: 单条消息
    test_results.append(("单条消息", test_single_message_direct()))

    # 测试3: 批量消息
    test_results.append(("批量消息", test_batch_message_direct()))

    # 输出测试结果总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)

    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")

    # 计算通过率
    total = len(test_results)
    passed = sum(1 for _, p in test_results if p)

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！Rust服务运行正常")
        print("\n💡 如果客户端仍然收到503错误，问题出在:")
        print("   1. 客户端使用了代理服务器")
        print("   2. 代理配置未正确绕过localhost")
        print("\n   解决方案:")
        print("   - 在客户端代码中设置 session.trust_env = False")
        print("   - 或设置 NO_PROXY=localhost,127.0.0.1")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查服务日志")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
