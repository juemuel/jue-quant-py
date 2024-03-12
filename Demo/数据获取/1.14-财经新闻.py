from datetime import datetime

import jieba
import jieba.analyse
import jieba.posseg as pseg
from snownlp import SnowNLP

from common import *

# 个股新闻接口
news_df = ak.stock_news_em(symbol='000651')
# 将发布时间列转换为日期时间类型
news_df['发布时间'] = pd.to_datetime(news_df['发布时间'])
print(news_df)

# 获取今天的日期
today = datetime.now().date()
# 使用日期过滤出今天的新闻
today_news = news_df[news_df['发布时间'].dt.date == today]
# 打印今天的新闻
print(today_news['新闻标题'])
print(today_news['新闻内容'])


def preprocess(txt):
	"""
	文本预处理以分词
	:param txt:
	:return:
	"""
	# 分词
	seg_list = jieba.lcut(txt)
	return seg_list


def sentiment_analysis(txt):
	"""
	情感分析
	:param txt:
	:return:
	"""
	s = SnowNLP(txt)
	# 情感得分，范围0-1，越接近1，表示越正面
	return s.sentiments


def extract_keyswords(txt, top_k=5):
	"""
	关键词提取
	:param txt:
	:param top_k:
	:return:
	"""
	# 提取关键词，默认返回前5个
	return jieba.analyse.extract_tags(txt, topK=top_k, withWeight=False, allowPOS=())


def named_entity_recognition(txt):
	"""
	命名实体识别
	:param txt:
	:return:
	"""
	words = pseg.cut(txt)
	entities = []
	for word, flag in words:
		# 识别人名，地名，机构，其他专名
		if flag in ['nr', 'ns', 'nt', 'nz']:
			entities.append((word, flag))
	return entities


def result(news):
	"""
	结果
	:param news:
	:return:
	"""
	print(f"分词结果：{preprocess(news)}")
	print(f"情感分析得分：{round(sentiment_analysis(news), 2)}")
	print(f"关键词提取：{extract_keyswords(news, top_k=3)}")
	print(f"命名实体识别：{named_entity_recognition(news)}")


# 对新闻标题进行分析
# today_news['新闻标题'].apply(lambda x: result(x))

# 财联社-电报接口
print(ak.stock_telegraph_cls())
# 新闻联播文字接口
# df = qs.news_cctv(start='20230609', end='20230609')
# print(df)
