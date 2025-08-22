import argparse
import threading
import time
import requests
from collections import defaultdict
import random

sample_texts = [
    "夜幕降临，城市的霓虹灯逐渐点亮，街道上行人匆匆，各自奔向不同的方向。远处传来悠扬的音乐声，似乎在诉说着这座城市不为人知的故事。",
    "山间的小路蜿蜒曲折，两旁的树木郁郁葱葱，阳光透过树叶的缝隙洒落在地上，形成斑驳的光影。清新的空气中夹杂着泥土和野花的芬芳，让人心旷神怡。",
    "大海波涛汹涌，浪花拍打着岩石，发出震耳欲聋的声响。远处的地平线上，太阳正缓缓沉入海面，将天空染成绚丽的橙红色，美得令人窒息。",
    "古老的图书馆内，书架高耸入天花板，空气中弥漫着纸张和墨水的气息。阳光透过彩色玻璃窗照进来，在地板上投下斑斓的光影，仿佛时光在此凝固。",
    "雪花纷纷扬扬地从天空中飘落，覆盖了整个小镇。孩子们在雪地里欢笑打闹，堆雪人、打雪仗，他们的笑声在寂静的冬日里格外清脆悦耳。",
    "战场上硝烟弥漫，士兵们紧握武器，眼神中充满了坚定与恐惧。炮火声不断在耳边响起，大地似乎都在颤抖，这是一场关乎生死的较量。",
    "实验室里，科学家们专注地观察着显微镜下的样本，记录着每一个微小的变化。他们知道，这项研究可能会改变人类对疾病认知的方式，拯救无数生命。",
    "宇宙飞船缓缓升空，突破大气层的束缚，进入浩瀚的太空。宇航员透过舷窗，看着渐渐变小的地球，内心充满了对未知世界的好奇和探索欲望。",
    "魔法学院的课堂上，年轻的巫师学徒们正在学习如何控制元素魔法。教授挥动魔杖，空气中出现了五彩斑斓的光芒，学生们惊叹不已，眼中闪烁着渴望。",
    "荒芜的沙漠中，一支商队缓缓前行，骆驼的铃铛声在寂静中回荡。烈日当空，热浪滚滚，但商人们依然坚定地向着绿洲的方向前进，希望在黄昏前到达。",
    "深山老林中，一座古老的寺庙静静矗立，青苔爬满了石阶和墙壁。晨钟响起，僧人们开始了一天的修行，诵经声在山谷中回荡，宁静而祥和。",
    "赛场上，运动员们摆好起跑姿势，全神贯注地等待发令枪响。观众席上鸦雀无声，空气仿佛凝固了。这一刻，时间似乎变得异常缓慢，每个人都屏住了呼吸。",
    "繁华的市集上，各种商品琳琅满目，小贩们吆喝着招揽顾客。空气中弥漫着香料、烤肉和新鲜水果的气息，人们讨价还价的声音此起彼伏，热闹非凡。",
    "废弃的工厂里，锈迹斑斑的机器静静地诉说着往日的繁忙。阳光透过破碎的窗户照进来，灰尘在光束中飞舞，仿佛时光的碎片在空中漂浮。",
    "雨后的森林，空气清新湿润，树叶上的水珠在阳光下闪闪发光。鸟儿在枝头欢快地歌唱，小溪的水流声潺潺，构成了一曲大自然的交响乐。",
    "古老的城堡矗立在山顶，经历了数百年风雨却依然坚固。石墙上爬满了常春藤，城堡的塔楼高耸入云，仿佛在守护着这片土地上的无数秘密和传说。",
    "未来的都市，高楼大厦直插云霄，飞行汽车在空中穿梭，全息投影的广告牌闪烁着五彩斑斓的光芒。人们的生活被科技深度改变，但内心的情感依然纯粹。",
    "小餐馆里，厨师熟练地翻炒着锅中的食材，香气四溢。食客们或独自品尝，或与朋友畅谈，餐厅内充满了欢声笑语和餐具碰撞的声音，温馨而热闹。",
    "深夜的医院走廊，医生和护士匆忙地穿梭于各个病房之间。急诊室的灯永远亮着，这里见证了无数生命的诞生与逝去，是希望与绝望交织的地方。",
    "音乐厅内，交响乐团正在演奏贝多芬的第九交响曲。指挥家挥动着指挥棒，音乐家们全神贯注地演奏着各自的乐器，美妙的旋律在空中流淌，感动着每一位听众。",
    "荒凉的外星球表面，探测车缓缓前行，收集着各种数据和样本。远处的恒星光芒黯淡，天空呈现出诡异的紫色，这里的一切都与地球截然不同，充满了神秘感。",
    "中世纪的集市上，商人们叫卖着各种商品，铁匠铺里传来叮叮当当的打铁声。吟游诗人在街头演唱着英雄的传说，人们围观聆听，暂时忘却了生活的艰辛。",
    "热带雨林中，各种奇特的植物竞相生长，形成了一个绿色的海洋。猴子在树枝间灵活跳跃，鸟儿展示着绚丽的羽毛，这里是地球上生物多样性最丰富的地方之一。",
    "地下洞穴中，钟乳石和石笋形成了奇特的景观，仿佛进入了一个神秘的地下王国。洞穴深处的地下河流缓缓流淌，水滴落在水面上的声音在寂静中格外清晰。",
    "高山之巅，云雾缭绕，远处的山峰若隐若现。登山者站在峰顶，俯瞰脚下的壮丽景色，感受着征服高山后的喜悦和成就感，这一刻所有的艰辛都变得值得。",
    "古老的钟表店里，各种钟表滴答作响，仿佛在演奏一曲时间的交响乐。老钟表匠戴着放大镜，专注地修理着一块古董怀表，他的手法精准而娴熟，令人叹为观止。",
    "战后的废墟中，人们开始重建家园，清理瓦砾，搭建临时住所。孩子们在废墟中找到了玩具，露出了久违的笑容，这是希望的种子在绝望中萌芽。",
    "童话世界里，会说话的动物和神奇的植物共同生活在一个和谐的王国。城堡里住着善良的公主和勇敢的王子，他们共同对抗邪恶的巫师，守护着这个美丽的世界。",
    "赛博朋克世界的街头，霓虹灯闪烁，全息投影的广告充斥着视野。人们身上植入了各种机械义肢和电子设备，科技与人体的界限变得模糊，但人性的光辉依然存在。",
    "古埃及的金字塔内部，墙壁上绘满了精美的壁画和象形文字，讲述着法老的故事和来世的旅程。考古学家小心翼翼地记录着每一个细节，试图解开这个古老文明的秘密。",
    "海底世界中，五彩斑斓的珊瑚礁形成了一个生机勃勃的生态系统。各种鱼类在珊瑚间穿梭，海龟悠闲地游过，这里是大自然创造的一幅绚丽多彩的水下画卷。",
    "中国古代的书院里，学子们正在诵读经典，研习圣贤之道。夜深人静时，他们点起油灯，继续埋头苦读，为的是有朝一日能够学以致用，造福百姓，光宗耀祖。",
    "西部荒野中，牛仔骑着马缓缓前行，远处是一望无际的草原和起伏的山丘。夕阳西下，天空被染成了金红色，牛仔的身影在这片广袤的土地上显得如此渺小而坚定。",
    "维多利亚时代的伦敦，雾气弥漫的街道上，马车来来往往，绅士们穿着礼服，女士们撑着阳伞。煤气灯的光芒在雾中显得朦胧而神秘，这是一个充满矛盾与变革的时代。",
    "未来的太空殖民地，巨大的穹顶下是一个微型的地球生态系统。人们在这里生活、工作、学习，透过穹顶可以看到浩瀚的星空和遥远的地球，这是人类探索宇宙的新起点。",
    "热闹的游乐园里，旋转木马、过山车和摩天轮吸引着无数游客。孩子们拿着棉花糖，脸上洋溢着纯真的笑容，大人们暂时放下了生活的压力，沉浸在欢乐的氛围中。",
    "中世纪的炼金术士实验室，各种奇怪的器具和瓶瓶罐罐摆满了桌面。炼金术士正在进行一项神秘的实验，希望能够发现长生不老的秘方或者点石成金的方法。",
    "日本传统的禅宗花园，石头和沙子被精心摆放，形成了一幅简约而深刻的画面。僧人们在此冥想修行，寻求内心的平静和智慧，远离尘世的喧嚣和烦扰。",
    "印度的传统婚礼现场，新娘身着红色纱丽，手臂上绘满了精美的海娜花纹。鼓声和音乐不断，亲友们载歌载舞，庆祝这对新人的结合，整个场面热闹而喜庆。",
    "非洲大草原上，狮群正在休息，雌狮警惕地观察着四周，保护着幼崽。远处的角马群正在迁徙，掀起阵阵尘土，这是一场生与死的较量，也是自然界生生不息的循环。",
    "巴黎的咖啡馆里，作家们聚在一起讨论文学和艺术，空气中弥漫着咖啡和香烟的气息。窗外是塞纳河和埃菲尔铁塔，这里孕育了无数伟大的思想和作品，影响了整个世界。",
    "古罗马的斗兽场内，角斗士们正在进行生死决斗，观众席上人山人海，欢呼声震耳欲聋。这是一个崇尚力量和勇气的时代，也是一个残酷而矛盾的文明。",
    "中国古代的皇宫内，宫女和太监们小心翼翼地行走在回廊上，生怕打扰了皇帝的休息。宫墙高耸，将内外隔绝，这里是权力的中心，也是无数人生死荣辱的决定之地。",
    "北欧的峡湾，陡峭的山崖直插入海，清澈的海水倒映着蓝天和白云。一艘维京长船缓缓驶过，船上的战士们正准备前往远方，探索未知的土地，开创新的家园。",
    "中东的集市上，香料、地毯和金银器皿琳琅满目，商人们热情地招呼着顾客。骆驼队从远方而来，带来了丝绸之路上的珍奇异宝，这里是东西方文化交融的重要枢纽。",
    "南美雨林中的古玛雅遗址，石头建筑被藤蔓缠绕，部分已经坍塌。考古学家们正在小心地挖掘和记录，试图揭开这个神秘文明消失的原因，了解他们的生活和信仰。",
    "澳大利亚的内陆沙漠，红色的土地一望无际，偶尔可见几棵顽强生长的树木。原住民在此生活了数万年，他们与这片看似贫瘠的土地建立了深厚的精神联系。",
    "南极科考站内，科学家们正在分析冰芯样本，研究地球气候的变化历史。外面是茫茫的冰雪世界，温度低至零下几十度，但人类的求知欲和探索精神让他们坚守在这里。",
    "文艺复兴时期的艺术家工作室，画家正在创作一幅宏大的油画，描绘神话或宗教场景。学徒们在一旁研磨颜料，准备画布，这里孕育了无数传世的艺术杰作，影响了后世代的审美和文化。",
    "中国江南水乡，小桥流水人家，乌篷船缓缓划过河面，岸边的柳树随风摇曳。居民们过着简单而安宁的生活，延续着几百年来的传统和习俗，构成了一幅诗情画意的东方画卷。"
]


class TTSStressTester:
    def __init__(self, urls, data, concurrency, requests_per_thread, test_type):
        self.urls = urls
        self.data = data
        self.concurrency = concurrency
        self.requests_per_thread = requests_per_thread
        self.test_type = test_type # digit: 12345.., en: one two three..., cn: generate_test_texts
        self.stats = {
            'total': 0,
            'success': 0,
            'fail': 0,
            'durations': [],
            'status_codes': defaultdict(int),
            'errors': defaultdict(int)
        }
        self.lock = threading.Lock()
        self.current_url_index = 0
        self.url_lock = threading.Lock()  # 用于轮询URL的锁
        self.text_length = 0

    def _get_next_url(self):
        with self.url_lock:
            url = self.urls[self.current_url_index]
            self.current_url_index = (self.current_url_index + 1) % len(self.urls)
        return url

    def _send_request(self):
        start_time = time.time()
        try:
            # 生成随机数字符串，确保不触发 vllm 的 cache
            if self.test_type == 'digit':
                self.data["text"] = ",".join(["".join([str(random.randint(0, 9)) for _ in range(5)]) for _ in range(5)])
            elif self.test_type == 'en':
                number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
                self.data["text"] = ", ".join([" ".join([number_words[random.randint(0, 9)] for _ in range(5)]) for _ in range(5)])
            elif self.test_type == 'cn':
                self.data["text"] = self.generate_one_test_text()
                self.input_length += len(self.data["text"])
            else:
                print(f"' test_type error ':=^20")
                return
            target_url = self._get_next_url()  # 获取轮询后的URL
            response = requests.post(target_url, json=self.data, timeout=10)
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
                else:
                    self.stats['fail'] += 1
                    
        except Exception as e:
            with self.lock:
                self.stats['fail'] += 1
                self.stats['errors'][str(type(e).__name__)] += 1
                self.stats['durations'].append(time.time() - start_time)

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

        print(f"\n吞吐量: {total_requests / total_time:.2f} 请求/秒")

    def generate_test_texts_list(self, count: int) -> list[str]:
        if count <= len(sample_texts):
            return sample_texts[:count]
        else:
            # 如果需要更多文本，则重复使用现有样本
            result = []
            for i in range(count):
                result.append(sample_texts[i % len(sample_texts)])
            return result

    def generate_one_test_text(self):
        return sample_texts[random.randint(0, len(sample_texts) - 1)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TTS服务压力测试脚本')
    parser.add_argument('--urls', nargs='+', 
                        default=['http://localhost:11996/tts'],  # , 'http://localhost:11997/tts'
                        help='TTS服务地址列表（多个用空格分隔）')
    parser.add_argument('--text', type=str, default='测试文本', help='需要合成的文本内容')
    parser.add_argument('--character', type=str, default='lancy', help='合成角色名称')
    parser.add_argument('--concurrency', type=int, default=16, help='并发线程数')
    parser.add_argument('--requests', type=int, default=5, help='每个线程的请求数')
    parser.add_argument('--test_type', type=str, default="digit", help='每个线程的请求数')
    
    args = parser.parse_args()
    
    test_data = {
        "text": args.text,
        "character": args.character
    }
    
    tester = TTSStressTester(
        urls=args.urls,
        data=test_data,
        concurrency=args.concurrency,
        requests_per_thread=args.requests
    )
    
    print(f"开始压力测试，配置参数：")
    print(f"目标服务: {', '.join(args.urls)}")
    print(f"并发线程: {args.concurrency}")
    print(f"单线程请求数: {args.requests}")
    print(f"总预计请求量: {args.concurrency * args.requests}")
    print(f"{' 测试启动 ':=^40}")
    
    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n测试被用户中断")