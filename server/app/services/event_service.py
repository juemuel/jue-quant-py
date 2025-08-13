from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import asyncio
from core.logger import logger

# 事件类型枚举
class EventType(Enum):
    NEWS = "news"                    # 财经新闻
    FINANCIAL_REPORT = "financial"   # 财务报告
    ANNOUNCEMENT = "announcement"    # 公司公告
    MARKET_SENTIMENT = "sentiment"   # 市场情绪
    MACRO_DATA = "macro"            # 宏观数据
    EARNINGS = "earnings"           # 业绩预告
    DIVIDEND = "dividend"           # 分红派息
    INSIDER_TRADING = "insider"     # 内幕交易
    ANALYST_RATING = "rating"       # 分析师评级

# 事件严重程度
class EventSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# 事件数据结构
@dataclass
class MarketEvent:
    event_id: str
    event_type: EventType
    symbol: str
    timestamp: datetime
    title: str
    content: str
    severity: EventSeverity
    sentiment_score: float  # -1到1，负数为负面，正数为正面
    keywords: List[str]
    source: str
    metadata: Dict[str, Any]

# 事件监听器基类
class EventListener(ABC):
    @abstractmethod
    async def listen(self) -> List[MarketEvent]:
        """监听并获取事件"""
        pass

# 新闻事件监听器
class NewsEventListener(EventListener):
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
    
    async def listen(self) -> List[MarketEvent]:
        """监听财经新闻事件"""
        events = []
        try:
            import akshare as ak
            from snownlp import SnowNLP
            
            for symbol in self.symbols:
                # 获取个股新闻
                news_df = ak.stock_news_em(symbol=symbol)
                
                for _, row in news_df.head(10).iterrows():  # 只取最新10条
                    # 情感分析
                    sentiment = SnowNLP(row['新闻标题'] + row['新闻内容']).sentiments
                    
                    # 关键词提取
                    import jieba.analyse
                    keywords = jieba.analyse.extract_tags(
                        row['新闻标题'] + row['新闻内容'], topK=5
                    )
                    
                    # 判断事件严重程度
                    severity = self._calculate_severity(row['新闻标题'], sentiment)
                    
                    event = MarketEvent(
                        event_id=f"news_{symbol}_{row['发布时间']}",
                        event_type=EventType.NEWS,
                        symbol=symbol,
                        timestamp=pd.to_datetime(row['发布时间']),
                        title=row['新闻标题'],
                        content=row['新闻内容'],
                        severity=severity,
                        sentiment_score=sentiment * 2 - 1,  # 转换为-1到1
                        keywords=keywords,
                        source="东方财富",
                        metadata={"url": row.get('新闻链接', '')}
                    )
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"新闻事件监听失败: {e}")
            
        return events
    
    def _calculate_severity(self, title: str, sentiment: float) -> EventSeverity:
        """根据标题和情感分析计算事件严重程度"""
        critical_keywords = ['重大', '紧急', '停牌', '退市', '违规', '调查']
        high_keywords = ['业绩', '财报', '分红', '重组', '收购']
        
        if any(keyword in title for keyword in critical_keywords):
            return EventSeverity.CRITICAL
        elif any(keyword in title for keyword in high_keywords):
            return EventSeverity.HIGH
        elif abs(sentiment - 0.5) > 0.3:  # 情感极端
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

# 财务事件监听器
class FinancialEventListener(EventListener):
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
    
    async def listen(self) -> List[MarketEvent]:
        """监听财务报告事件"""
        events = []
        try:
            import akshare as ak
            
            for symbol in self.symbols:
                # 获取财务报告披露时间
                disclosure_df = ak.stock_report_disclosure(market="沪深京", period="2024年报")
                
                # 筛选当前股票
                stock_disclosure = disclosure_df[disclosure_df['股票代码'] == symbol]
                
                for _, row in stock_disclosure.iterrows():
                    event = MarketEvent(
                        event_id=f"financial_{symbol}_{row['预约披露日期']}",
                        event_type=EventType.FINANCIAL_REPORT,
                        symbol=symbol,
                        timestamp=pd.to_datetime(row['预约披露日期']),
                        title=f"{row['股票简称']}财报披露",
                        content=f"预约披露日期：{row['预约披露日期']}",
                        severity=EventSeverity.HIGH,
                        sentiment_score=0.0,
                        keywords=['财报', '披露'],
                        source="巨潮资讯",
                        metadata={"report_type": "年报"}
                    )
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"财务事件监听失败: {e}")
            
        return events

# 事件处理器
class EventProcessor:
    def __init__(self):
        self.event_filters = []
        self.event_analyzers = []
    
    def add_filter(self, filter_func):
        """添加事件过滤器"""
        self.event_filters.append(filter_func)
    
    def add_analyzer(self, analyzer_func):
        """添加事件分析器"""
        self.event_analyzers.append(analyzer_func)
    
    def process_events(self, events: List[MarketEvent]) -> List[MarketEvent]:
        """处理事件列表"""
        # 1. 过滤事件
        filtered_events = events
        for filter_func in self.event_filters:
            filtered_events = filter_func(filtered_events)
        
        # 2. 分析事件
        for analyzer_func in self.event_analyzers:
            filtered_events = analyzer_func(filtered_events)
        
        return filtered_events

# 事件驱动策略管理器
class EventDrivenStrategyManager:
    def __init__(self):
        self.listeners = []
        self.processor = EventProcessor()
        from .signal_service import EventSignalGenerator
        self.signal_generator = EventSignalGenerator()
        self.is_running = False
    
    def add_listener(self, listener: EventListener):
        """添加事件监听器"""
        self.listeners.append(listener)
    
    async def start_monitoring(self, interval: int = 300):  # 5分钟检查一次
        """开始事件监控"""
        self.is_running = True
        logger.info("事件驱动监控已启动")
        
        while self.is_running:
            try:
                all_events = []
                
                # 收集所有监听器的事件
                for listener in self.listeners:
                    events = await listener.listen()
                    all_events.extend(events)
                
                if all_events:
                    # 处理事件
                    processed_events = self.processor.process_events(all_events)
                    
                    # 生成信号
                    signals = self.signal_generator.generate_signals(processed_events)
                    
                    if signals:
                        logger.info(f"生成了 {len(signals)} 个事件驱动信号")
                        # 这里可以调用回测或实盘交易
                        await self._execute_signals(signals)
                
                # 等待下次检查
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"事件监控出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _execute_signals(self, signals: List[Dict]):
        """执行信号（可以对接回测或实盘）"""
        for signal in signals:
            logger.info(f"执行信号: {signal}")
            # 这里可以调用现有的回测函数
            # 或者发送到实盘交易系统
    
    def stop_monitoring(self):
        """停止事件监控"""
        self.is_running = False
        logger.info("事件驱动监控已停止")