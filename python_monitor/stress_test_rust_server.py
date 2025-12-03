#!/usr/bin/env python3
"""
Rust服务端压力测试程序
用于模拟瞬间高流量攻击，测试系统极限和崩溃点

⚠️  安全警告：此程序仅用于压力测试和系统验证
请确保在受控环境中使用，避免对生产系统造成影响
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import sys
import argparse
import signal

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

class StressTester:
    """Rust服务端压力测试器"""

    def __init__(self, target_url="http://localhost:8080", num_workers=50, duration=60):
        self.target_url = target_url
        self.num_workers = num_workers
        self.duration = duration
        self.running = True
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'timeout_requests': 0,
            'response_times': [],
            'error_types': {},
            'status_codes': {}
        }

    def generate_random_message(self):
        """生成随机的测试消息"""
        channels = [
            -1002115686230,  # Pump Alert - GMGN
            -1002096576678,  # Happy Nuts
            -1002040892468,  # Gake's Bakes
            -1002011100964,  # Happy Channel
            -1001419575394,  # Wizzy's Trades
            -1001104204833,  # Solidot
            52504489         # Bot
        ]

        # 生成随机加密货币相关内容
        crypto_keywords = [
            "PUMP", "DUMP", "MOON", "HODL", "BUY", "SELL", "TOKEN", "COIN",
            "CONTRACT", "ADDRESS", "LIQUIDITY", "SWAP", "TRADE"
        ]

        # 生成随机消息内容
        message_length = random.randint(50, 500)
        words = []

        # 添加加密货币关键词
        num_keywords = random.randint(2, 5)
        for _ in range(num_keywords):
            words.append(random.choice(crypto_keywords))

        # 添加随机文本
        for _ in range(message_length // 10):
            word = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(3, 10)))
            words.append(word)

        random.shuffle(words)
        text = ' '.join(words)

        # 添加合约地址格式
        if random.random() > 0.3:
            contract = '0x' + ''.join(random.choices('0123456789abcdef', k=40))
            text += f" Contract: {contract}"

        return {
            "channel_id": random.choice(channels),
            "channel_name": f"TestChannel_{random.randint(1, 100)}",
            "message_id": random.randint(100000, 999999),
            "text": text,
            "timestamp": int(time.time()),
            "sender": f"TestUser_{random.randint(1, 1000)}"
        }

    async def send_request(self, session, message_data, request_id):
        """发送单个请求"""
        start_time = time.time()

        try:
            # 随机延迟，模拟真实负载
            if random.random() > 0.7:
                await asyncio.sleep(random.uniform(0.001, 0.1))

            # 添加随机超时
            timeout = aiohttp.ClientTimeout(total=random.uniform(2, 10))

            async with session.post(
                f"{self.target_url}/api/v1/message",
                json=message_data,
                timeout=timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': f'StressTester-{request_id}'
                }
            ) as response:
                response_time = time.time() - start_time

                self.stats['total_requests'] += 1
                self.stats['response_times'].append(response_time)

                # 记录状态码
                status_code = response.status
                self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1

                if response.status == 200:
                    self.stats['successful_requests'] += 1
                    try:
                        result = await response.json()
                        logger.debug(f"请求成功: {request_id}, 响应时间: {response_time:.3f}s")
                    except:
                        logger.debug(f"请求成功但无JSON响应: {request_id}")
                else:
                    self.stats['failed_requests'] += 1
                    error_text = await response.text()
                    logger.warning(f"请求失败: {request_id}, 状态码: {status_code}, 错误: {error_text[:100]}")

                    # 记录错误类型
                    error_key = f"HTTP_{status_code}"
                    self.stats['error_types'][error_key] = self.stats['error_types'].get(error_key, 0) + 1

        except asyncio.TimeoutError:
            self.stats['timeout_requests'] += 1
            self.stats['failed_requests'] += 1
            self.stats['total_requests'] += 1
            logger.error(f"请求超时: {request_id}")

        except Exception as e:
            self.stats['failed_requests'] += 1
            self.stats['total_requests'] += 1
            error_type = type(e).__name__
            self.stats['error_types'][error_type] = self.stats['error_types'].get(error_type, 0) + 1
            logger.error(f"请求异常: {request_id}, 错误: {e}")

    async def worker(self, worker_id, session):
        """工作协程，持续发送请求"""
        logger.info(f"工作线程 {worker_id} 启动")
        request_count = 0

        while self.running:
            try:
                # 生成测试消息
                message_data = self.generate_random_message()

                # 发送请求
                request_id = f"{worker_id}_{request_count}"
                await self.send_request(session, message_data, request_id)

                request_count += 1

                # 随机间隔，模拟突发流量
                if random.random() > 0.3:
                    # 70%的概率快速连续发送
                    await asyncio.sleep(random.uniform(0.001, 0.01))
                else:
                    # 30%的概率稍作停顿
                    await asyncio.sleep(random.uniform(0.01, 0.1))

            except Exception as e:
                logger.error(f"工作线程 {worker_id} 异常: {e}")
                await asyncio.sleep(0.1)  # 异常后短暂停顿

    async def stats_reporter(self):
        """统计报告协程"""
        start_time = time.time()
        last_report_time = start_time

        while self.running:
            await asyncio.sleep(5)  # 每5秒报告一次

            current_time = time.time()
            elapsed = current_time - start_time

            if self.stats['response_times']:
                avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
                max_response_time = max(self.stats['response_times'])
                min_response_time = min(self.stats['response_times'])
            else:
                avg_response_time = max_response_time = min_response_time = 0

            # 计算RPS（每秒请求数）
            rps = self.stats['total_requests'] / elapsed if elapsed > 0 else 0

            logger.info(f"=" * 60)
            logger.info(f"📊 实时统计报告")
            logger.info(f"⏱️  运行时间: {elapsed:.1f}秒")
            logger.info(f"🚀 总请求数: {self.stats['total_requests']}")
            logger.info(f"✅ 成功请求: {self.stats['successful_requests']} ({self.stats['successful_requests']/self.stats['total_requests']*100:.1f}%)")
            logger.info(f"❌ 失败请求: {self.stats['failed_requests']} ({self.stats['failed_requests']/self.stats['total_requests']*100:.1f}%)")
            logger.info(f"⏰ 超时请求: {self.stats['timeout_requests']}")
            logger.info(f"📈 请求速率: {rps:.2f} RPS")
            logger.info(f"⏱️  平均响应时间: {avg_response_time*1000:.1f}ms")
            logger.info(f"⏱️  最大响应时间: {max_response_time*1000:.1f}ms")
            logger.info(f"⏱️  最小响应时间: {min_response_time*1000:.1f}ms")

            if self.stats['status_codes']:
                logger.info(f"📋 状态码分布: {dict(list(self.stats['status_codes'].items())[:5])}")

            if self.stats['error_types']:
                logger.info(f"⚠️  错误类型: {dict(list(self.stats['error_types'].items())[:5])}")

            logger.info(f"=" * 60)

    async def run_stress_test(self):
        """运行压力测试"""
        logger.info(f"🚀 启动压力测试")
        logger.info(f"🎯 目标URL: {self.target_url}")
        logger.info(f"👥 工作线程: {self.num_workers}")
        logger.info(f"⏱️  测试时长: {self.duration}秒")
        logger.info(f"💣 测试模式: 高并发 + 突发流量")
        logger.info("")

        # 启动统计报告协程
        stats_task = asyncio.create_task(self.stats_reporter())

        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=100,  # 连接池限制
            limit_per_host=50,  # 每个主机连接限制
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=5)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:

            # 启动工作协程
            workers = []
            for i in range(self.num_workers):
                worker_task = asyncio.create_task(self.worker(i, session))
                workers.append(worker_task)

            logger.info(f"✅ {self.num_workers}个工作协程已启动")
            logger.info(f"🔄 开始发送请求...")
            logger.info("")

            # 等待测试完成或手动中断
            try:
                await asyncio.sleep(self.duration)
            except KeyboardInterrupt:
                logger.info("\n⚠️  收到中断信号，正在停止测试...")
            finally:
                self.running = False

            # 等待所有工作协程完成
            logger.info("⏳ 等待工作协程完成...")
            await asyncio.gather(*workers, return_exceptions=True)

            # 停止统计报告
            stats_task.cancel()
            try:
                await stats_task
            except asyncio.CancelledError:
                pass

        # 生成最终报告
        await self.generate_final_report()

    async def generate_final_report(self):
        """生成最终测试报告"""
        logger.info(f"\n" + "=" * 80)
        logger.info(f"🏁 压力测试完成！最终报告")
        logger.info(f"=" * 80)

        total_time = self.duration
        total_requests = self.stats['total_requests']
        successful_requests = self.stats['successful_requests']
        failed_requests = self.stats['failed_requests']

        logger.info(f"📊 测试总结：")
        logger.info(f"  ⏱️  总运行时间: {total_time}秒")
        logger.info(f"  🚀 总请求数: {total_requests}")
        logger.info(f"  ✅ 成功请求: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
        logger.info(f"  ❌ 失败请求: {failed_requests} ({failed_requests/total_requests*100:.1f}%)")
        logger.info(f"  📈 平均请求速率: {total_requests/total_time:.2f} RPS")
        logger.info(f"  🎯 并发度: {self.num_workers}个工作线程")

        if self.stats['response_times']:
            avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            max_response_time = max(self.stats['response_times'])
            min_response_time = min(self.stats['response_times'])

            logger.info(f"\n⏱️  响应时间统计：")
            logger.info(f"  📊 平均响应时间: {avg_response_time*1000:.1f}ms")
            logger.info(f"  📈 最大响应时间: {max_response_time*1000:.1f}ms")
            logger.info(f"  📉 最小响应时间: {min_response_time*1000:.1f}ms")

        if self.stats['error_types']:
            logger.info(f"\n⚠️  错误统计：")
            for error_type, count in sorted(self.stats['error_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"  {error_type}: {count}次")

        if self.stats['status_codes']:
            logger.info(f"\n📋 HTTP状态码分布：")
            for status_code, count in sorted(self.stats['status_codes'].items()):
                logger.info(f"  {status_code}: {count}次")

        # 系统稳定性评估
        if failed_requests == 0:
            logger.success(f"\n✅ 系统稳定性：优秀 - 无失败请求")
        elif failed_requests/total_requests < 0.01:
            logger.success(f"\n✅ 系统稳定性：良好 - 失败率<1%")
        elif failed_requests/total_requests < 0.05:
            logger.warning(f"\n⚠️  系统稳定性：一般 - 失败率<5%")
        else:
            logger.error(f"\n❌ 系统稳定性：较差 - 失败率{failed_requests/total_requests*100:.1f}%")

        logger.info(f"=" * 80)
        logger.info(f"💡 建议：")
        logger.info(f"  🔧 根据测试结果优化系统配置")
        logger.info(f"  📊 分析失败原因并改进错误处理")
        logger.info(f"  🛡️  添加限流和防护机制")
        logger.info(f"=" * 80)

class AdvancedStressTester(StressTester):
    """高级压力测试器，支持更多攻击模式"""

    def generate_malicious_payload(self):
        """生成恶意载荷，测试系统防护能力"""
        attack_types = [
            "oversized_message",
            "rapid_fire",
            "connection_flood",
            "memory_bomb",
            "cpu_intensive"
        ]

        attack_type = random.choice(attack_types)

        if attack_type == "oversized_message":
            # 超大消息（1MB+）
            return {
                "channel_id": -1002115686230,
                "channel_name": "A" * 1000,
                "message_id": random.randint(100000, 999999),
                "text": "X" * (1024 * 1024),  # 1MB文本
                "timestamp": int(time.time()),
                "sender": "B" * 1000
            }

        elif attack_type == "memory_bomb":
            # 内存炸弹 - 包含大量重复数据
            base_text = "PUMP_ALERT_" * 1000
            return {
                "channel_id": -1002115686230,
                "channel_name": "PumpAlert-MemoryTest",
                "message_id": random.randint(100000, 999999),
                "text": base_text * 50,  # 50KB重复文本
                "timestamp": int(time.time()),
                "sender": "MemoryBombTest"
            }

        elif attack_type == "cpu_intensive":
            # CPU密集型内容 - 包含复杂模式
            complex_pattern = ""
            for i in range(1000):
                complex_pattern += f"Contract{i}: 0x{''.join(random.choices('0123456789abcdef', k=40))} "

            return {
                "channel_id": -1002115686230,
                "channel_name": "CPU-Intensive-Test",
                "message_id": random.randint(100000, 999999),
                "text": complex_pattern,
                "timestamp": int(time.time()),
                "sender": "CPU-Intensive-Sender"
            }

        else:
            # 默认返回普通测试消息
            return self.generate_random_message()

    async def send_malicious_request(self, session, request_id):
        """发送恶意请求"""
        if random.random() > 0.3:  # 30%概率发送恶意载荷
            message_data = self.generate_malicious_payload()
        else:
            message_data = self.generate_random_message()

        await self.send_request(session, message_data, request_id)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Rust服务端压力测试工具")
    parser.add_argument("--url", "-u", default="http://localhost:8080", help="目标Rust服务URL")
    parser.add_argument("--workers", "-w", type=int, default=50, help="并发工作线程数")
    parser.add_argument("--duration", "-d", type=int, default=60, help="测试持续时间（秒）")
    parser.add_argument("--malicious", "-m", action="store_true", help="启用恶意载荷测试")
    parser.add_argument("--advanced", "-a", action="store_true", help="使用高级攻击模式")

    args = parser.parse_args()

    # 选择测试器类型
    if args.advanced:
        tester = AdvancedStressTester(args.url, args.workers, args.duration)
    else:
        tester = StressTester(args.url, args.workers, args.duration)

    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("\n⚠️  收到中断信号，正在优雅停止...")
        tester.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行测试
    try:
        asyncio.run(tester.run_stress_test())
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()