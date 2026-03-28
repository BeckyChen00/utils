import os
import re
import argparse
from collections import Counter

import matplotlib.pyplot as plt
from wordcloud import WordCloud

try:
    import nltk
    from nltk.corpus import stopwords
except Exception:
    nltk = None


def load_domains(path):
    """读取域名文本文件"""
    with open(path, encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    return lines


def prepare_stopwords():
    """准备停用词（英文+自定义通用词）"""
    sw = set()
    if nltk:
        try:
            stopwords.words('english')
        except Exception:
            nltk.download('stopwords')
        sw = set(stopwords.words('english'))
    # 添加自定义通用无意义词汇
    custom_stopwords = {
        "system", "generation","ai","finder","data","self","systems", "management", "platform", "platforms", "service", "services", 
        "analysis", "solution", "solutions", "tool", "tools", "application", "applications", 
        "software", "technology", "technologies", "framework", "frameworks",
        "app", "apps", "website", "websites", "program", "programs", "project", "projects", 
        "e", "g", "etc", "managing", "using", "based", "related", "online", "for", "with", "and"
    }
    sw.update(custom_stopwords)
    return sw


def get_word_frequencies(domains, stopwords_set):
    """清洗文本并精确统计词频"""
    word_counts = Counter()
    
    for d in domains:
        # 移除非字母字符，将其替换为空格
        clean_text = re.sub(r"[^a-zA-Z\s]", " ", d)
        
        # 分词
        words = clean_text.split()
        
        for w in words:
            w_lower = w.lower()
            # 过滤单字符、停用词
            if len(w_lower) > 1 and w_lower not in stopwords_set:
                # 统计词频（使用首字母大写形式，增加科研图表高级感）
                word_counts[w_lower.title()] += 1
                
    return dict(word_counts)


def generate_wordcloud(frequencies, outpath):
    """核心：生成词云图并保存（无白边版本）"""
    # 使用柔和的科研风格配色方案，按词频高低排序
    colors = [
        '#313555',  # 词频最高：深蓝色
        '#d59261',  # 词频次高：橙棕色
        '#3e838d',  # 词频中等：青蓝色
        '#a84337',  # 词频较低：红棕色
        '#ece0c8',  # 词频最低：浅米色
    ]
    
    # 按照词频从高到低对单词进行排序，获取排序后的单词列表
    sorted_words = sorted(frequencies.keys(), key=lambda w: frequencies[w], reverse=True)
    
    # 自定义颜色函数：按排名指数分层，确保大词颜色丰富且背景小词退后
    def frequency_color_func(word, *args, **kwargs):
        try:
            rank = sorted_words.index(word)
            # 排名第 1 的最大词：深蓝
            if rank < 1:
                return colors[0]
            # 排名第 2-4 的次大词：橙棕
            elif rank < 4:
                return colors[1]
            # 排名第 5-15 的中大词：青蓝
            elif rank < 15:
                return colors[2]
            # 排名第 16-50 的中等词：红棕
            elif rank < 50:
                return colors[3]
            # 剩下的 250 个小词作为背景填充：浅米色
            else:
                return colors[4]
        except ValueError:
            return colors[-1]

    wc = WordCloud(
        width=1200, height=300,
        background_color='white',
        font_path=os.path.join(os.path.dirname(__file__) or '.', 'LeagueGothic-Regular.ttf'),
        max_words=300,
        max_font_size=180,
        min_font_size=10,
        margin=1,
        prefer_horizontal=0.8,
        color_func=frequency_color_func,
        random_state=42
    ).generate_from_frequencies(frequencies)
    
    # 关键：创建无任何边距的画布
    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    
    # 👇 这行是消除白边的核心代码
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    plt.savefig(outpath, dpi=150, bbox_inches='tight', pad_inches=0)
    plt.close()
    return outpath


def main():
    parser = argparse.ArgumentParser(description='仅生成域名词云图')
    parser.add_argument('domains_file', help='域名文本文件路径，如 domains.txt')
    parser.add_argument('--outdir', default='wordcloud_results', help='词云图输出目录')
    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.outdir, exist_ok=True)

    # 1. 读取域名数据
    domains = load_domains(args.domains_file)

    # 2. 准备停用词
    stopwords_set = prepare_stopwords()

    # 3. 清洗文本（去除无意义词汇）并精确统计词频
    frequencies = get_word_frequencies(domains, stopwords_set)

    # # 4. 生成并保存词云图
    wc_path = os.path.join(args.outdir, 'domains_wordcloud2.png')
    generate_wordcloud(frequencies, wc_path)

    print('词云图已保存至:', wc_path)


if __name__ == '__main__':
    main()