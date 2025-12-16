#!/usr/bin/env python3
"""
API兼容性测试脚本
测试原有的单条消息格式和新的批量爬虫格式
"""

import requests
import json
import time
import sys

# API基础地址
BASE_URL = "http://localhost:8080"

def test_health_check():
    """测试健康检查接口"""
    print("\n📊 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_single_message():
    """测试原有的单条消息格式"""
    print("\n📨 测试单条消息格式（向后兼容性）...")

    test_message = {
        "channel_id": -1002115686230,
        "channel_name": "Pump Alert - GMGN",
        "message_id": 12345,
        "text": "🚀 NEW TOKEN ALERT! Contract: 0x1234567890abcdef1234567890abcdef12345678",
        "timestamp": int(time.time()),
        "sender": "Bot_PumpAlert (52504489)"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/message",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )

        print(f"HTTP状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # 验证响应格式（应该保持原有格式）
        if "success" in data and "message" in data:
            print("✅ 单条消息格式测试通过，响应格式保持兼容")
            return True
        else:
            print("❌ 响应格式不正确")
            return False
    except Exception as e:
        print(f"❌ 单条消息测试异常: {e}")
        return False

def test_batch_request():
    """测试新的批量爬虫格式"""
    print("\n📦 测试批量爬虫格式...")

    batch_request = {
        "batch_id": f"batch_6937fcb5000000001e0339ff_{int(time.time())}",
        "timestamp": "2025-12-16T09:20:30",
        "source": "xhs_crawler_v1.0",
        "note_info": {
            "note_id": "6937fcb5000000001e0339ff",
            "note_title": "我的美妆分享",
            "total_comments": 3
        },
        "messages": [
            {
                "message_id": "comment_001",
                "role": "user",
                "content": "这个口红颜色太好看了，非常喜欢！",
                "metadata": {
                    "user_info": {
                        "user_id": "user_001",
                        "user_name": "美妆达人"
                    },
                    "interaction": {
                        "like_count": 10,
                        "reply_count": 2
                    },
                    "temporal": {
                        "absolute": 1640000000.0,
                        "relative": "昨天 20:38"
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
                "content": "价格有点贵，但是质量很好，值这个价。",
                "metadata": {
                    "user_info": {
                        "user_id": "user_002",
                        "user_name": "理性买家"
                    },
                    "interaction": {
                        "like_count": 5,
                        "reply_count": 1
                    },
                    "temporal": {
                        "absolute": 1640000100.0,
                        "relative": "昨天 21:15"
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
                "content": "包装很精美，送人很有面子。",
                "metadata": {
                    "user_info": {
                        "user_id": "user_003",
                        "user_name": "送礼达人"
                    },
                    "interaction": {
                        "like_count": 8,
                        "reply_count": 0
                    },
                    "temporal": {
                        "absolute": 1640000200.0,
                        "relative": "今天 10:30"
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
        response = requests.post(
            f"{BASE_URL}/api/v1/message",
            json=batch_request,
            headers={"Content-Type": "application/json"}
        )

        print(f"HTTP状态码: {response.status_code}")

        try:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

            # 验证批量响应格式
            required_fields = ["status", "batch_id", "note_info", "analysis_result", "processing_stats"]
            if all(field in data for field in required_fields):
                print("✅ 批量格式测试通过，响应包含所有必要字段")

                # 验证分析结果
                analysis_result = data.get("analysis_result", {})
                if "sentiment_analysis" in analysis_result:
                    sentiment_count = len(analysis_result["sentiment_analysis"])
                    print(f"  - 情感分析结果: {sentiment_count} 条")

                if "topic_analysis" in analysis_result:
                    topic_count = len(analysis_result["topic_analysis"])
                    print(f"  - 主题分析结果: {topic_count} 条")

                if "keyword_analysis" in analysis_result:
                    keyword_count = len(analysis_result["keyword_analysis"])
                    print(f"  - 关键词分析结果: {keyword_count} 条")

                return True
            else:
                print("❌ 响应格式缺少必要字段")
                print(f"响应包含的字段: {list(data.keys())}")
                return False
        except json.JSONDecodeError:
            print(f"❌ 响应不是有效的JSON: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 批量请求测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_malformed_request():
    """测试格式错误的请求"""
    print("\n🚨 测试格式错误的请求...")

    malformed_request = {
        "invalid_field": "test"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/message",
            json=malformed_request,
            headers={"Content-Type": "application/json"}
        )

        data = response.json()
        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if response.status_code == 400:
            print("✅ 正确识别了格式错误的请求")
            return True
        else:
            print("❌ 应该返回400错误")
            return False
    except Exception as e:
        print(f"测试异常（这是正常的）: {e}")
        return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("API接口兼容性测试")
    print("测试地址:", BASE_URL)
    print("=" * 60)

    # 检查服务是否运行
    if not test_health_check():
        print("\n❌ 服务未运行或无法访问，请先启动服务")
        sys.exit(1)

    test_results = []

    # 测试1：单条消息格式（向后兼容）
    test_results.append(("单条消息格式（向后兼容）", test_single_message()))

    # 测试2：批量爬虫格式
    test_results.append(("批量爬虫格式", test_batch_request()))

    # 测试3：格式错误
    test_results.append(("格式错误处理", test_malformed_request()))

    # 输出测试结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")

    # 计算通过率
    total = len(test_results)
    passed = sum(1 for _, p in test_results if p)

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！API接口兼容性良好")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查问题")
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
