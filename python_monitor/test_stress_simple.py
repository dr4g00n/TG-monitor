#!/usr/bin/env python3
"""
简单版Rust服务端压力测试程序
轻量级实现，快速测试系统压力承受能力
"""

import requests
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

def generate_test_message():
    """生成测试消息"""
    channels = [
        -1002115686230, -1002096576678, -1002040892468,
        -1002011100964, -1001419575394, -1001104204833, 52504489
    ]

    return {
        "channel_id": random.choice(channels),
        "channel_name": f"StressTest_{random.randint(1, 100)}",
        "message_id": random.randint(100000, 999999),
        "text": f"STRESS TEST PUMP ALERT {random.randint(1, 1000)} " * 10,
        "timestamp": int(time.time()),
        "sender": f"StressUser_{random.randint(1, 100)}"
    }

def send_request(url, message_data, request_id):
    """发送单个请求"""
    try:
        response = requests.post(
            f"{url}/api/v1/message",
            json=message_data,
            timeout=5,
            headers={'Content-Type': 'application/json'}
        )
        return {
            'id': request_id,
            'status': response.status_code,
            'time': time.time(),
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'id': request_id,
            'status': 'ERROR',
            'time': time.time(),
            'success': False,
            'error': str(e)
        }

def run_stress_test(url="http://localhost:8080", num_threads=20, duration=30):
    """运行简单压力测试"""
    print(f"🚀 启动简单压力测试")
    print(f"🎯 目标: {url}")
    print(f"👥 线程数: {num_threads}")
    print(f"⏱️  持续时间: {duration}秒")
    print("=" * 50)

    start_time = time.time()
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'response_times': []
    }

    def worker(worker_id):
        """工作线程"""
        local_stats = {'total': 0, 'success': 0, 'failed': 0}
        request_id = 0

        while time.time() - start_time < duration:
            message_data = generate_test_message()
            result = send_request(url, message_data, f"{worker_id}_{request_id}")

            local_stats['total'] += 1
            if result['success']:
                local_stats['success'] += 1
            else:
                local_stats['failed'] += 1

            request_id += 1

            # 快速连续发送，制造压力
            if random.random() > 0.5:
                time.sleep(0.001)  # 1ms延迟

        return local_stats

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交所有工作线程
        futures = [executor.submit(worker, i) for i in range(num_threads)]

        # 收集结果
        for future in as_completed(futures):
            local_stats = future.result()
            stats['total'] += local_stats['total']
            stats['success'] += local_stats['success']
            stats['failed'] += local_stats['failed']

    # 生成报告
    elapsed = time.time() - start_time
    rps = stats['total'] / elapsed if elapsed > 0 else 0

    print(f"\n🏁 测试完成！")
    print(f"=" * 50)
    print(f"📊 测试结果：")
    print(f"  ⏱️  运行时间: {elapsed:.1f}秒")
    print(f"  🚀 总请求数: {stats['total']}")
    print(f"  ✅ 成功请求: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"  ❌ 失败请求: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    print(f"  📈 请求速率: {rps:.2f} RPS")
    print(f"  🎯 并发度: {num_threads}线程")

    if stats['failed'] == 0:
        print(f"\n✅ 系统稳定性：优秀")
    elif stats['failed']/stats['total'] < 0.05:
        print(f"\n⚠️  系统稳定性：良好")
    else:
        print(f"\n❌ 系统稳定性：需要优化")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="简单Rust服务端压力测试")
    parser.add_argument("--url", "-u", default="http://localhost:8080", help="目标URL")
    parser.add_argument("--threads", "-t", type=int, default=20, help="并发线程数")
    parser.add_argument("--duration", "-d", type=int, default=30, help="测试时长（秒）")

    args = parser.parse_args()

    print(f"\n🚀 Rust服务端压力测试工具")
    print(f"🎯 目标: {args.url}")
    print(f"👥 并发: {args.threads}线程")
    print(f"⏱️  时长: {args.duration}秒")
    print("=" * 50)

    try:
        run_stress_test(args.url, args.threads, args.duration)
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被中断")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    main()