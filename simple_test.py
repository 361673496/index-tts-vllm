import argparse
import threading
import time
import requests
from collections import defaultdict
import random

from text2test import sample_texts, sample_texts_long


class TTSStressTester:
    def __init__(self, urls, data, concurrency, requests_per_thread, test_type, interface, debug=False, text_source="normal"):
        self.urls = urls
        self.data = data
        self.concurrency = concurrency
        self.requests_per_thread = requests_per_thread
        self.test_type = test_type # digit: 12345.., en: one two three..., cn: generate_test_texts
        self.interface = interface  # tts or cosyvoice
        self.debug = debug  # 调试模式
        self.text_source = text_source  # normal 或 long，用于选择文本库
        self.stats = {
            'total': 0,
            'success': 0,
            'fail': 0,
            'durations': [],
            'status_codes': defaultdict(int),
            'errors': defaultdict(int),
            'error_details': []  # 记录详细错误信息
        }
        self.lock = threading.Lock()
        self.current_url_index = 0
        self.url_lock = threading.Lock()  # 用于轮询URL的锁
        self.text_length = 0
        self.request_count = 0  # 请求计数器

    def _get_next_url(self):
        with self.url_lock:
            url = self.urls[self.current_url_index]
            self.current_url_index = (self.current_url_index + 1) % len(self.urls)
        return url

    def _build_request_data(self, text_content):
        """根据接口类型构建请求数据"""
        if self.interface == 'tts':
            # 原有的tts接口格式
            return {
                "text": text_content,
                "character": self.data.get("character", "jay_klee")
            }
        elif self.interface == 'cosyvoice':
            # cosyvoice接口格式
            return {
                "text": text_content,
                "mode": "zero_shot",
                "prompt_audio_path": "/mnt/oss/甜美女孩-15s.mp3",
                "prompt_text": "希望你以后能够做的比我还好呦。",
                "speed": 1.0,
                "stream": False,
                "output_format": "wav",
                "zero_shot_spk_id": "sweet_girl_15s",
                "bit_rate": 192000,
                "compression_level": 2
            }
        else:
            raise ValueError(f"Unsupported interface type: {self.interface}")

    def _send_request(self):
        start_time = time.time()
        try:
            # 生成随机数字符串，确保不触发 vllm 的 cache
            if self.test_type == 'digit':
                text_content = ",".join(["".join([str(random.randint(0, 9)) for _ in range(5)]) for _ in range(5)])
            elif self.test_type == 'en':
                number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
                text_content = ", ".join([" ".join([number_words[random.randint(0, 9)] for _ in range(5)]) for _ in range(5)])
            elif self.test_type == 'cn':
                text_content = self.generate_one_test_text()
                self.text_length += len(text_content)
            else:
                print(f"' test_type error ':=^20")
                return
            
            # 根据接口类型构建请求数据
            request_data = self._build_request_data(text_content)
            target_url = self._get_next_url()  # 获取轮询后的URL
            
            # 设置请求头
            headers = {'Content-Type': 'application/json'}
            
            # 调试信息：打印第一次请求的详细信息
            with self.lock:
                self.request_count += 1
                if self.debug and self.request_count == 1:
                    print(f"\n=== 第一次请求调试信息 ===")
                    print(f"URL: {target_url}")
                    print(f"Headers: {headers}")
                    print(f"Request Data: {request_data}")
                    print("========================\n")
            
            # 发送请求
            response = requests.post(target_url, json=request_data, headers=headers, timeout=300)
            elapsed = time.time() - start_time
            
            with self.lock:
                self.stats['durations'].append(elapsed)
                self.stats['status_codes'][response.status_code] += 1
                self.stats['total'] += 1
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'audio' in content_type:
                        self.stats['success'] += 1
                    else:
                        self.stats['fail'] += 1
                        self.stats['errors']['invalid_content_type'] += 1
                        # 记录详细错误信息
                        try:
                            error_detail = f"HTTP {response.status_code} - Invalid Content-Type: {content_type} - Response: {response.text[:500]}"
                            self.stats['error_details'].append(error_detail)
                        except:
                            pass
                else:
                    self.stats['fail'] += 1
                    # 记录详细错误信息
                    try:
                        error_detail = f"HTTP {response.status_code} - URL: {target_url} - Response: {response.text[:500]}"
                        self.stats['error_details'].append(error_detail)
                    except:
                        error_detail = f"HTTP {response.status_code} - URL: {target_url} - Response: Unable to decode response"
                        self.stats['error_details'].append(error_detail)
                    
        except Exception as e:
            with self.lock:
                self.stats['fail'] += 1
                self.stats['errors'][str(type(e).__name__)] += 1
                self.stats['durations'].append(time.time() - start_time)
                # 记录详细错误信息
                error_detail = f"Exception: {type(e).__name__} - {str(e)} - URL: {target_url if 'target_url' in locals() else 'unknown'}"
                self.stats['error_details'].append(error_detail)

    def _worker(self):
        for _ in range(self.requests_per_thread):
            self._send_request()

    def run(self):
        threads = []
        start_time = time.time()
        
        for _ in range(self.concurrency):
            thread = threading.Thread(target=self._worker)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time
        self._generate_report(total_time)

    def _generate_report(self, total_time):
        durations = self.stats['durations']
        total_requests = self.stats['total']
        
        print(f"\n{' 测试报告 ':=^40}")
        print(f"接口类型: {self.interface}")
        print(f"总请求时间: {total_time:.2f}秒")
        if self.test_type == 'en':
            print(f"WPS: {self.concurrency * self.requests_per_thread * 25 / total_time:.2f}秒")
            print(f"WPM: {self.concurrency * self.requests_per_thread * 25 * 60 / total_time:.2f}秒")
        elif self.test_type == 'cn':
            print(f"WPS: {self.text_length / total_time:.2f}秒")
            print(f"WPM: {self.text_length * 60 / total_time:.2f}秒")
        print(f"总请求量: {total_requests}")
        print(f"成功请求: {self.stats['success']}")
        print(f"失败请求: {self.stats['fail']}")
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            print(f"\n响应时间统计:")
            print(f"平均: {avg_duration:.3f}秒")
            print(f"最大: {max_duration:.3f}秒")
            print(f"最小: {min_duration:.3f}秒")
            
            sorted_durations = sorted(durations)
            for p in [50, 90, 95, 99]:
                index = int(p / 100 * len(sorted_durations))
                print(f"P{p}: {sorted_durations[index]:.3f}秒")

        print("\n状态码分布:")
        for code, count in self.stats['status_codes'].items():
            print(f"HTTP {code}: {count}次")

        if self.stats['errors']:
            print("\n错误统计:")
            for error, count in self.stats['errors'].items():
                print(f"{error}: {count}次")

        # 显示详细错误信息（最多显示前10个错误）
        if self.stats['error_details']:
            print(f"\n详细错误信息（显示前10个）:")
            for i, error_detail in enumerate(self.stats['error_details'][:10]):
                print(f"{i+1}. {error_detail}")
            if len(self.stats['error_details']) > 10:
                print(f"... 还有 {len(self.stats['error_details']) - 10} 个类似错误")

        print(f"\n吞吐量: {total_requests / total_time:.2f} 请求/秒")

    def generate_test_texts_list(self, count: int) -> list[str]:
        # 根据text_source选择文本库
        texts = sample_texts_long if self.text_source == "long" else sample_texts
        
        if count <= len(texts):
            return texts[:count]
        else:
            # 如果需要更多文本，则重复使用现有样本
            result = []
            for i in range(count):
                result.append(texts[i % len(texts)])
            return result

    def generate_one_test_text(self):
        # 根据text_source选择文本库
        texts = sample_texts_long if self.text_source == "long" else sample_texts
        return texts[random.randint(0, len(texts) - 1)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TTS服务压力测试脚本')
    parser.add_argument('--urls', nargs='+', 
                        default=['http://localhost:11996/tts'],  # , 'http://localhost:11997/tts'
                        help='TTS服务地址列表（多个用空格分隔）')
    parser.add_argument('--text', type=str, default='测试文本', help='需要合成的文本内容')
    parser.add_argument('--character', type=str, default='jay_klee', help='合成角色名称')
    parser.add_argument('--concurrency', type=int, default=16, help='并发线程数')
    parser.add_argument('--requests', type=int, default=5, help='每个线程的请求数')
    parser.add_argument('--test_type', type=str, default="digit", help='测试文本类型（digit/en/cn）')
    parser.add_argument('--interface', type=str, default="tts", choices=['tts', 'cosyvoice'], 
                        help='接口类型（tts/cosyvoice）')
    parser.add_argument('--debug', action='store_true', 
                        help='启用调试模式，显示第一次请求的详细信息')
    parser.add_argument('--text_source', type=str, default="normal", choices=['normal', 'long'],
                        help='文本源类型（normal: 使用sample_texts, long: 使用sample_texts_long）')
    
    args = parser.parse_args()
    
    test_data = {
        "text": args.text,
        "character": args.character
    }
    
    tester = TTSStressTester(
        urls=args.urls,
        data=test_data,
        concurrency=args.concurrency,
        requests_per_thread=args.requests,
        test_type=args.test_type,
        interface=args.interface,
        debug=args.debug,
        text_source=args.text_source
    )
    
    print(f"开始压力测试，配置参数：")
    print(f"接口类型: {args.interface}")
    print(f"目标服务: {', '.join(args.urls)}")
    print(f"并发线程: {args.concurrency}")
    print(f"单线程请求数: {args.requests}")
    print(f"文本源类型: {args.text_source}")
    print(f"总预计请求量: {args.concurrency * args.requests}")
    print(f"{' 测试启动 ':=^40}")
    
    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n测试被用户中断")