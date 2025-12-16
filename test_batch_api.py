#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量评论分析API测试脚本
用于验证 /api/v1/message 接口的批量请求功能
"""

import requests
import json
import time
from datetime import datetime
import sys

def test_batch_api(base_url="http://localhost:8080"):
    """测试批量评论分析接口"""

    print("=" * 60)
    print("批量评论分析API测试")
    print("=" * 60)

    # 禁用代理
    session = requests.Session()
    session.trust_env = False

    # 1. 健康检查
    print("\n[1] 检查服务健康状态...")
    try:
        response = session.get(f"{base_url}/health", timeout=10)
        print(f"✓ 健康检查成功: {response.status_code}")
        print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False

    # 2. 准备批量请求数据
    print("\n[2] 准备批量评论数据...")

    batch_request = {
        "batch_id": f"batch_test_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "source": "test_crawler_v1.0",
        "note_info": {
            "note_id": "test_note_001",
            "note_title": "测试商品评论分析",
            "total_comments": 3
        },
        "messages": [
            {
                "message_id": "comment_001",
                "role": "user",
                "content": "这个产品的质量真的很不错，包装也很精美，物流很快！",
                "metadata": {
                    "user_info": {
                        "user_id": "user_001",
                        "user_name": "小明"
                    },
                    "interaction": {
                        "like_count": 15,
                        "reply_count": 3
                    },
                    "temporal": {
                        "absolute": 1640000000.0,
                        "relative": "2小时前"
                    },
                    "location": {
                        "country": "中国",
                        "city": "上海"
                    }
                }
            },
            {
                "message_id": "comment_002",
                "role": "user",
                "content": "价格有点贵，但是一分钱一分货，总的来说性价比还可以。",
                "metadata": {
                    "user_info": {
                        "user_id": "user_002",
                        "user_name": "理性消费者"
                    },
                    "interaction": {
                        "like_count": 8,
                        "reply_count": 1
                    },
                    "temporal": {
                        "absolute": 1640000100.0,
                        "relative": "3小时前"
                    },
                    "location": {
                        "country": "中国",
                        "city": "北京"
                    }
                }
            },
            {
                "message_id": "comment_003",
                "role": "user",
                "content": "客服态度很差，问个问题半天不回复，体验不好。",
                "metadata": {
                    "user_info": {
                        "user_id": "user_003",
                        "user_name": "用户C"
                    },
                    "interaction": {
                        "like_count": 3,
                        "reply_count": 2
                    },
                    "temporal": {
                        "absolute": 1640000200.0,
                        "relative": "今天 15:30"
                    },
                    "location": {
                        "country": "中国",
                        "city": "上海"  # 使用字符串而非None
                    }
                }
            }
        ]
    }

    # 验证JSON格式
    print("  验证JSON格式...")
    try:
        json_str = json.dumps(batch_request)
        print(f"✓ JSON格式正确，共 {len(json_str)} 字节")
    except Exception as e:
        print(f"✗ JSON格式错误: {e}")
        return False

    print("\n[3] 发送批量请求到API...")
    print(f"  API URL: {base_url}/api/v1/message")
    print(f"  请求方法: POST")
    print(f"  Content-Type: application/json")
    print(f"  数据大小: {len(json.dumps(batch_request))} 字节")

    try:
        response = session.post(
            f"{base_url}/api/v1/message",
            json=batch_request,
            timeout=30
        )

        print(f"\n[4] 收到响应...")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {response.elapsed.total_seconds():.3f} 秒")

        # 解析响应
        try:
            result = response.json()
            print(f"\n[5] 响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 验证响应格式
            if "status" in result:
                if result["status"] == "success":
                    print("\n✅ 测试成功！批量请求被正确处理")
                    return True
                else:
                    print(f"\n❌ 处理失败，状态: {result['status']}")
                    if "error_message" in result:
                        print(f"  错误信息: {result['error_message']}")
                    return False
            else:
                print("\n❌ 响应格式不正确，缺少 status 字段")
                return False

        except json.JSONDecodeError as e:
            print(f"\n❌ 响应不是有效的JSON: {e}")
            print(f"  原始响应: {response.text[:500]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {type(e).__name__}: {e}")
        return False

def test_validations():
    """测试各种验证场景"""

    print("\n" + "=" * 60)
    print("验证测试")
    print("=" * 60)

    session = requests.Session()
    session.trust_env = False

    base_url = "http://localhost:8080"

    # 测试1: 缺少 user_info
    print("\n[测试1] 缺少 user_info 字段...")
    invalid_request = {
        "batch_id": "test_missing_userinfo",
        "timestamp": datetime.now().isoformat(),
        "source": "test",
        "note_info": {
            "note_id": "test",
            "note_title": "测试",
            "total_comments": 1
        },
        "messages": [{
            "message_id": "c1",
            "role": "user",
            "content": "test",
            "metadata": {
                # 缺少 user_info
                "interaction": {"like_count": 0, "reply_count": 0},
                "temporal": {"absolute": 0, "relative": ""},
                "location": {"country": "中国", "city": "北京"}
            }
        }]
    }

    try:
        response = session.post(f"{base_url}/api/v1/message", json=invalid_request)
        result = response.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False)}")
        if "missing field" in result.get("error_message", ""):
            print("  ✓ 正确捕获缺少字段错误")
    except Exception as e:
        print(f"  错误: {e}")

    # 测试2: JSON格式错误
    print("\n[测试2] JSON格式不完整的场景...")
    try:
        # 故意发送不完整的JSON
        import json
        incomplete_json = json.dumps(invalid_request)[:-10]  # 删除最后10个字符

        response = session.post(
            f"{base_url}/api/v1/message",
            data=incomplete_json,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False)}")
    except Exception as e:
        print(f"  预期错误: {type(e).__name__}")

if __name__ == "__main__":
    print("TG Monitor 批量评论分析API测试脚本")
    print("===================================\n")

    # 检查服务是否运行
    print("检查服务状态...")
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✓ 服务运行正常\n")
        else:
            print(f"✗ 服务返回异常状态码: {response.status_code}\n")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 无法连接服务: {e}")
        print("请确保服务已在运行: ./target/release/tg-meme-token-monitor")
        sys.exit(1)

    # 运行API测试
    success = test_batch_api()

    # 运行验证测试
    test_validations()

    # 总结
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 测试失败，请检查日志")
    print("=" * 60)

    sys.exit(0 if success else 1)
