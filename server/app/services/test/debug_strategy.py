import sys
import os

from pkg_resources import non_empty_lines
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from app.services.data_service import get_stock_history
from app.services.indicator_service import IndicatorCalculator
from app.services.strategy_service import generate_ma_crossover_signal_from_indicators, generate_rsi_signal_from_indicators
from app.services.strategy_service import generate_unified_signals
from app.services.event_service import MarketEvent, EventType, EventSeverity
from datetime import datetime as dt
import datetime  # 修改这行：导入完整的datetime模块
import pandas as pd
from core.logger import logger
# 添加Excel导出功能
import openpyxl
# =========== 公用方法 ===========
def get_and_preprocess_stock_data(source="akshare", code="000001", market="SH", 
                                 start_date="20240801", end_date="20241201", page_size=1000):
    """
    获取并预处理股票数据的通用方法
    返回: (success: bool, df: DataFrame, message: str)
    """
    # 1. 获取股票历史数据
    result = get_stock_history(
        source=source, code=code, market=market,
        start_date=start_date, end_date=end_date, page_size=page_size
    )
    
    if result.get('status') != 'success':
        return False, None, f"数据获取失败: {result.get('message')}"
    
    # 2. 提取数据并转换为DataFrame
    data_info = result.get('data', {})
    data_list = data_info.get('list', [])
    
    if not data_list:
        return False, None, "没有获取到实际数据"
    
    df = pd.DataFrame(data_list)
    
    # 3. 检查必要列
    required_columns = ['收盘价', '日期']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, None, f"缺少必要的列: {missing_columns}"
    
    # 4. 数据预处理
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    df['收盘价'] = pd.to_numeric(df['收盘价'], errors='coerce')
    
    # 删除无效数据
    nan_count = df['收盘价'].isna().sum()
    if nan_count > 0:
        df = df.dropna(subset=['收盘价'])
    
    # 为analytic_service准备数据
    df['收盘'] = df['收盘价']
    
    return True, df, f"成功获取并预处理 {len(df)} 行数据"
def ensure_numeric_columns(df, columns):
    """
    确保指定列为数值类型的通用方法
    """
    df_copy = df.copy()
    for col in columns:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    return df_copy
def analyze_basic_signals(signal_df, signal_name="信号", display_columns=None):
    """
    分析和显示信号统计的通用方法
    """
    if 'signal' not in signal_df.columns:
        return f"错误：{signal_name}数据中没有signal列"
    
    # 确保signal列为数值类型
    df_copy = signal_df.copy()
    df_copy['signal'] = pd.to_numeric(df_copy['signal'], errors='coerce').fillna(0)
    
    # 统计信号
    buy_signals = df_copy[df_copy['signal'] == 1]
    sell_signals = df_copy[df_copy['signal'] == -1]
    non_zero_signals = df_copy[df_copy['signal'] != 0]

    result = f"\n=== {signal_name}统计分析 ===\n"
    result += f"买入信号数量: {len(buy_signals)}\n"
    result += f"卖出信号数量: {len(sell_signals)}\n"
    
    if len(non_zero_signals) > 0:
        result += f"\n所有{signal_name}非零信号 ({len(non_zero_signals)}个)，前10如下：\n"
        if display_columns:
            available_cols = [col for col in display_columns if col in df_copy.columns]
            result += non_zero_signals[available_cols].head(10).to_string()
        else:
            result += non_zero_signals.head(10).to_string()
    else:
        result += f"\n没有生成任何{signal_name}"
    
    return result
def calculate_and_validate_indicator(df, calculator_method, indicator_name, **kwargs):
    """
    计算技术指标并验证结果的通用方法
    使用新的 IndicatorCalculator
    """
    try:
        # 创建计算器实例
        calculator = IndicatorCalculator()
        
        # 调用计算器方法
        result = calculator_method(calculator, df, **kwargs)
        
        if result.get('status') != 'success':
            return False, None, f"{indicator_name}计算失败: {result.get('message')}"
        
        data_list = result.get('data', [])
        if not data_list:
            return False, None, f"{indicator_name}计算返回空数据"
        
        indicator_df = pd.DataFrame(data_list)
        return True, indicator_df, f"{indicator_name}计算成功"
        
    except Exception as e:
        return False, None, f"{indicator_name}计算异常: {str(e)}"
def analyze_unified_signals(unified_result):
    """
    分析统一信号生成结果
    """
    if unified_result['status'] != 'success':
        return f"❌ 统一信号生成失败: {unified_result.get('message')}"
    
    data = unified_result['data']
    unified_signals = data['unified_signals']
    
    result = "\n=== 统一信号生成分析 ===\n"
    result += f"✓ 数据驱动信号数量: {data['data_signals_count']}\n"
    result += f"✓ 事件驱动信号数量: {data['event_signals_count']}\n"
    result += f"✓ 统一后总信号数量: {data['total_signals']}\n"
    
    # 分析信号类型分布
    if unified_signals:
        signal_types = {}
        signal_strengths = []
        
        for signal in unified_signals:
            signal_type = signal.get('type', 'unknown')
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            strength = signal.get('strength', 0)
            if strength > 0:
                signal_strengths.append(strength)
        
        result += "\n统一后的信号类型分布:\n"
        for sig_type, count in signal_types.items():
            result += f"  - {sig_type}: {count}个\n"
        
        if signal_strengths:
            avg_strength = sum(signal_strengths) / len(signal_strengths)
            result += f"\n平均信号强度: {avg_strength:.3f}\n"
            result += f"最强信号强度: {max(signal_strengths):.3f}\n"
            result += f"最弱信号强度: {min(signal_strengths):.3f}\n"
        
        # 显示前5个信号详情
        result += "\n前10个统一信号详情:\n"
        for i, signal in enumerate(unified_signals[:10]):
            signal_type = signal.get('signal_type', 'unknown')
            direction = signal.get('direction', 0)
            reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'N/A'))
            result += f"  {i+1}. 类型: {signal_type}({direction}), "
            result += f"强度: {signal.get('strength', 0):.3f}, "
            result += f"时间: {signal.get('timestamp', 'N/A')}\n"
            result += f"     原因: {reason}\n"
    
    return result
def create_mock_events_data(df=None, event_count=20):
    """
    创建模拟事件数据用于测试
    
    Args:
        start_date: 开始日期，格式 "YYYYMMDD"
        end_date: 结束日期，格式 "YYYYMMDD"
        event_count: 要生成的事件数量
    """
    import random
    
    if df is None or df.empty:
        # 如果没有提供DataFrame，使用默认日期范围
        start_dt = datetime.datetime(2024, 1, 1)
        end_dt = datetime.datetime(2024, 12, 1)
    else:
        # 从DataFrame中提取日期范围
        if '日期' in df.columns:
            dates = pd.to_datetime(df['日期'])
            start_dt = dates.min().to_pydatetime()
            end_dt = dates.max().to_pydatetime()
        else:
            # 如果没有日期列，使用默认范围
            start_dt = datetime.datetime(2024, 1, 1)
            end_dt = datetime.datetime(2024, 12, 1)
    
    # 计算日期范围
    date_range = (end_dt - start_dt).days
    if date_range <= 0:
        date_range = 365  # 默认一年范围
    
    mock_events = []
    
    # 定义事件模板
    # 修改事件模板，增加更多样化的数据
    event_templates = [
        {
            "type": EventType.NEWS,
            "titles": ["重大合作协议签署", "新产品发布会成功举办", "业绩大幅增长", "获得重要奖项"],
            "sentiment_range": (0.6, 0.9),  # 提高正面情感范围
            "severity": EventSeverity.HIGH   # 提高严重程度
        },
        {
            "type": EventType.NEWS,
            "titles": ["监管调查启动", "重大违规事件", "业绩大幅下滑", "高管离职风波"],
            "sentiment_range": (-0.9, -0.6),  # 提高负面情感范围
            "severity": EventSeverity.HIGH     # 提高严重程度
        },
        {
            "type": EventType.EARNINGS,
            "titles": ["即将发布季度财报", "年度业绩预告", "中期业绩说明会", "投资者关系活动"],
            "sentiment_range": (-0.3, 0.7),   # 扩大情感范围
            "severity": EventSeverity.MEDIUM
        }
    ]
    
    # 生成指定数量的事件
    for i in range(event_count):
        # 随机选择事件模板
        template = random.choice(event_templates)
        
        # 随机生成日期
        random_days = random.randint(0, date_range)
        event_date = start_dt + datetime.timedelta(days=random_days)
        
        # 随机选择标题和情感分数
        title = random.choice(template["titles"])
        sentiment_min, sentiment_max = template["sentiment_range"]
        sentiment_score = random.uniform(sentiment_min, sentiment_max)
        
        # 创建事件
        event = MarketEvent(
            event_id=f"event_{i+1:03d}",
            event_type=template["type"],
            symbol="000001",
            timestamp=event_date,
            title=title,
            content=f"{title}的详细内容描述",
            severity=template["severity"],
            sentiment_score=sentiment_score,
            keywords=title.split(),
            source="模拟数据源",
            metadata={"event_index": i+1, "template_type": template["type"].value}
        )
        
        mock_events.append(event)
    
    # 按时间排序
    mock_events.sort(key=lambda x: x.timestamp)
    
    return mock_events
# ============ 基础单信号生成(使用strategy_service中的单一信号的生成函数) ============
# MA使用简单的金叉死叉判断,固定使用MA5和MA20
# RSI固定阈值超卖30,超买70,触及就生成
def debug_basic_strategy_flow():

    """
    使用封装方法的简化版基础策略流程调试
    """
    print("=== 开始调试基础策略流程（简化版）===")
    
    try:
        # 1. 获取和预处理数据
        success, df, message = get_and_preprocess_stock_data()
        if not success:
            print(f"数据准备失败: {message}")
            return
        print(f"✓ {message}")
        
        # 2. 计算移动平均线
        success, df_with_ma, message = calculate_and_validate_indicator(
            df, IndicatorCalculator.calculate_moving_averages, "移动平均线", periods=[5, 20]
        )
        if not success:
            print(f"✗ {message}")
            return
        print(f"✓ {message}")
        
        # 确保数值类型
        # 确保数值类型 - 注意新的列名格式是 SMA5, SMA20
        df_with_ma = ensure_numeric_columns(df_with_ma, ['收盘价', '收盘', 'SMA5', 'SMA20'])
        
        # 重命名列以保持兼容性
        if 'SMA5' in df_with_ma.columns:
            df_with_ma['MA5'] = df_with_ma['SMA5']
        if 'SMA20' in df_with_ma.columns:
            df_with_ma['MA20'] = df_with_ma['SMA20']
            
        # 3. 计算RSI
        success, df_with_rsi, message = calculate_and_validate_indicator(
            df, IndicatorCalculator.calculate_rsi, "RSI指标", period=14
        )
        if not success:
            print(f"✗ {message}")
            df_with_rsi = df_with_ma  # 使用MA数据继续
        else:
            print(f"✓ {message}")
            df_with_rsi = ensure_numeric_columns(df_with_rsi, ['收盘价', '收盘', 'RSI'])
        
        # 初始化信号变量
        ma_signals_row = []
        rsi_signals_row = []
        # 4. 生成MA交叉信号
        # 在生成MA信号前添加调试信息
        logger.debug(f"[Service]df_with_ma列: {df_with_ma.columns.tolist()}")
        logger.info(f"[DebugBasicStrategy]开始生成MA交叉信号，数据行数: {len(df_with_ma)}")
        logger.info(f"[DebugBasicStrategy]MA5长度: {len(df_with_ma['MA5']) if 'MA5' in df_with_ma.columns else 0}, MA20长度: {len(df_with_ma['MA20']) if 'MA20' in df_with_ma.columns else 0}")
        ma_signal_result = generate_ma_crossover_signal_from_indicators(df_with_ma, short_period=5, long_period=20)
        if ma_signal_result['status'] == 'success':
            ma_signals_row = ma_signal_result['data']
            signal_df = pd.DataFrame(ma_signals_row)
            print(analyze_basic_signals(signal_df, "MA交叉信号", ['日期', 'MA5', 'MA20', 'signal']))
        logger.info(f"[DebugBasicStrategy]MA交叉信号数量（含零）: {len(ma_signals_row)}")
        # 5. 生成RSI信号
        # 在生成RSI信号前添加调试信息
        logger.info(f"[DebugBasicStrategy]df_with_rsi列: {df_with_rsi.columns.tolist()}")
        logger.info(f"[DebugBasicStrategy]开始生成RSI信号，RSI长度: {len(df_with_rsi['RSI14']) if 'RSI14' in df_with_rsi.columns else 0}")
        rsi_signal_result = generate_rsi_signal_from_indicators(df_with_rsi, period=14, oversold=30, overbought=70)
        if rsi_signal_result['status'] == 'success':
            rsi_signals_row = rsi_signal_result['data']
            signal_df = pd.DataFrame(rsi_signals_row)
            print(analyze_basic_signals(signal_df, "RSI信号", ['日期', '收盘价', 'RSI', 'signal']))
        # 导出Excel文件 - 基础策略流程
        try:
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            excel_file = f"basic_strategy_signals_{timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 导出MA信号
                if ma_signals_row:
                    ma_df = pd.DataFrame(ma_signals_row)
                    ma_df.to_excel(writer, sheet_name='MA_Signals', index=False)
                    print(f"✓ MA信号已导出到 {excel_file} - MA_Signals sheet")
                
                # 导出RSI信号
                if rsi_signals_row:
                    rsi_df = pd.DataFrame(rsi_signals_row)
                    rsi_df.to_excel(writer, sheet_name='RSI_Signals', index=False)
                    print(f"✓ RSI信号已导出到 {excel_file} - RSI_Signals sheet")
                
                # 导出原始数据(携带指标)
                df_with_rsi.to_excel(writer, sheet_name='Raw_Data', index=False)
                print(f"✓ 原始数据已导出到 {excel_file} - Raw_Data sheet")
                
            print(f"\n📊 基础策略信号已保存到: {excel_file}")
        except Exception as e:
                logger.error(f"导出Excel文件失败: {e}")
                print(f"❌ Excel导出失败: {e}")
        print("\n=== 基础策略流程调试完成 ===")
        # 统计非零信号 - 修正过滤逻辑
        def is_nonzero_signal(signal_dict):
            signal_value = signal_dict.get('signal', 0)
            # 处理各种可能的零值表示
            if signal_value is None:
                return False
            if isinstance(signal_value, str):
                try:
                    signal_value = float(signal_value)
                except (ValueError, TypeError):
                    return False
            return signal_value != 0 and signal_value != 0.0
        
        ma_nonzero = [s for s in ma_signals_row if is_nonzero_signal(s)]
        rsi_nonzero = [s for s in rsi_signals_row if is_nonzero_signal(s)]
        
        logger.info(f"[DebugBasicStrategy]MA非零信号数量: {len(ma_nonzero)}")
        logger.info(f"[DebugBasicStrategy]RSI非零信号数量: {len(rsi_nonzero)}")
        logger.info(f"[DebugBasicStrategy]总非零信号数量: {len(ma_nonzero) + len(rsi_nonzero)}")
        
    except Exception as e:
        logger.error(f"调试过程中发生错误: {e}")
        print(f"\n错误: {e}")

# ============ 统一信号生成 ============
# 数据驱动中使用MA和RSI,事件驱动中使用新闻情感和财报发布
# 默认MA信号生成:MA5/MA20;
# 默认RSI信号生成:周期14,超买超卖30/70; 并且需要满足成交量volume > avg_volume * 1.2
def debug_unified_signals():
    """
    调试统一信号生成器
    """
    print("=== 开始调试统一信号生成器 ===")
    
    try:
        # 1. 获取和预处理数据
        print("\n1. 获取和预处理股票数据...")
        success, df, message = get_and_preprocess_stock_data()
        if not success:
            print(f"❌ 数据准备失败: {message}")
            return
        print(f"✓ {message}")
        
        # 2. 创建模拟事件数据
        print("\n2. 创建模拟事件数据...")
        dates = pd.to_datetime(df['日期'])
        start_dt = dates.min().to_pydatetime()
        end_dt = dates.max().to_pydatetime()
        print(f"股票数据时间范围: {start_dt} ~ {end_dt}")
        events_data = create_mock_events_data(
            df,
            event_count=300
        )
        print(f"✓ 创建了 {len(events_data)} 个模拟事件")
        print(f"✓ 事件时间范围: {events_data[0].timestamp.strftime('%Y-%m-%d')} 到 {events_data[-1].timestamp.strftime('%Y-%m-%d')}")
        # 3. 配置信号生成参数
        print("\n3. 配置信号生成参数...")
        
        # 数据驱动信号规则配置
        data_signal_config = {
            'ma_crossover': {
                'enable': True,
                'use_parameterized': False,  # 改为False，使用固定参数版本，与debug_basic_strategy_flow一致
                'short_period': 5,           # 与debug_basic_strategy_flow相同
                'long_period': 20,           # 与debug_basic_strategy_flow相同
                'adaptive': True,
                'filter_config': {
                    'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 1},  # 禁用过滤器
                    'volume_confirmation': {'enable': False, 'volume_multiplier': 1, 'lookback_days': 20},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            },
            'rsi': {
                'enable': True,
                'use_parameterized': False,  # 改为False，使用固定参数版本
                'period': 14,                # 与debug_basic_strategy_flow相同
                'oversold': 30,              # 与debug_basic_strategy_flow相同
                'overbought': 70,            # 与debug_basic_strategy_flow相同
                'filter_config': {
                    'volume_confirmation': {'enable': False, 'volume_multiplier': 1, 'lookback_days': 20},  # 禁用过滤器
                    'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 0.5},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            }
        }
        # 事件驱动信号规则配置
        event_signal_config = {
            'news_sentiment': {
                'enable': True,
                'use_parameterized': True,  # 使用参数化版本
                'sentiment_threshold': 0.8,  # 自定义阈值
                'severity_levels': [EventSeverity.HIGH, EventSeverity.CRITICAL]
            },
            'earnings': {
                'enable': True,
                'use_parameterized': False  # 使用固定参数版本
            },
            'keyword_trigger': {
                'enable': True,
                'use_parameterized': True,  # 使用参数化版本
                'positive_keywords': ['突破', '创新高', '利好'],
                'negative_keywords': ['暴跌', '亏损', '风险'],
                'strength': 0.7,
            }
        }
        print("✓ 信号配置完成")
        print(f"  - 数据驱动信号: MA交叉({data_signal_config['ma_crossover']['short_period']},{data_signal_config['ma_crossover']['long_period']}), RSI({data_signal_config['rsi']['period']})")
         # 安全地访问事件信号配置
        news_threshold = event_signal_config.get('news_sentiment', {}).get('sentiment_threshold', '默认')
        earnings_info = "参数化" if event_signal_config.get('earnings', {}).get('use_parameterized', False) else "固定参数"
        keyword_strength = event_signal_config.get('keyword_trigger', {}).get('strength', '默认')
        print(f"  - 事件驱动信号: 新闻情绪(阈值{news_threshold}), 财报预期({earnings_info}), 关键词触发(强度{keyword_strength})")

        print("\n4. 生成统一信号...")
        # 4.1 生成统一组合信号
        # unified_result = generate_unified_signals(
        #     price_data=df,
        #     events_data=events_data,
        #     data_signal_config=data_signal_config,
        #     event_signal_config=event_signal_config
        # )
        # print(analyze_unified_signals(unified_result))
        # 4.2 生成仅数据驱动的信号
        data_only_result = generate_unified_signals(
            price_data=df,
            events_data=None,  # 不提供事件数据
            data_signal_config=data_signal_config,
            event_signal_config=None
        )
        print(analyze_unified_signals(data_only_result))
        # 4.3 生成仅事件驱动的信号
        # event_only_result = generate_unified_signals(
        #     price_data=df,
        #     events_data=events_data,
        #     data_signal_config=None,
        #     event_signal_config=event_signal_config
        # )
        # print(analyze_unified_signals(event_only_result))
        # 4.4 生成默认配置的信号
        # default_result = generate_unified_signals(price_data=df, events_data=events_data)
        # print(analyze_unified_signals(default_result))
        
        # 5. 分析结果
        # 5. 导出到Excel文件
        print("\n5. 导出数据到Excel...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = f"unified_signals_debug_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 5.1 导出股票历史数据
                print("  - 导出股票历史数据...")
                df.to_excel(writer, sheet_name='股票历史数据', index=False)
                
                # 5.2 导出data_signals（如果存在）
                if 'data' in data_only_result and 'data_signals' in data_only_result['data']:
                    data_signals = data_only_result['data']['data_signals']
                    if data_signals:
                        print(f"  - 导出数据信号 ({len(data_signals)}条)...")
                        if isinstance(data_signals, list) and len(data_signals) > 0:
                            # 检查第一个元素的结构
                            if isinstance(data_signals[0], dict):
                                data_signals_df = pd.DataFrame(data_signals)
                            else:
                                # 如果不是字典列表，创建简单的DataFrame
                                data_signals_df = pd.DataFrame({'信号': data_signals})
                        else:
                            data_signals_df = pd.DataFrame({'提示': ['无数据信号']})
                        data_signals_df.to_excel(writer, sheet_name='数据信号', index=False)
                    else:
                        # 创建空的数据信号表
                        empty_df = pd.DataFrame({'提示': ['无数据信号']})
                        empty_df.to_excel(writer, sheet_name='数据信号', index=False)
                else:
                    # 创建空的数据信号表
                    empty_df = pd.DataFrame({'提示': ['无数据信号']})
                    empty_df.to_excel(writer, sheet_name='数据信号', index=False)
                
                # 5.3 导出event_signals（如果存在）
                if 'data' in data_only_result and 'event_signals' in data_only_result['data']:
                    event_signals = data_only_result['data']['event_signals']
                    if event_signals:
                        print(f"  - 导出事件信号 ({len(event_signals)}条)...")
                        if isinstance(event_signals, list) and len(event_signals) > 0:
                            if isinstance(event_signals[0], dict):
                                event_signals_df = pd.DataFrame(event_signals)
                            else:
                                event_signals_df = pd.DataFrame({'信号': event_signals})
                        else:
                            event_signals_df = pd.DataFrame({'提示': ['无事件信号']})
                        event_signals_df.to_excel(writer, sheet_name='事件信号', index=False)
                    else:
                        # 创建空的事件信号表
                        empty_df = pd.DataFrame({'提示': ['无事件信号']})
                        empty_df.to_excel(writer, sheet_name='事件信号', index=False)
                else:
                    # 创建空的事件信号表
                    empty_df = pd.DataFrame({'提示': ['无事件信号']})
                    empty_df.to_excel(writer, sheet_name='事件信号', index=False)
                
                # 5.4 导出unified_signals
                if 'data' in data_only_result and 'unified_signals' in data_only_result['data']:
                    unified_signals = data_only_result['data']['unified_signals']
                    if unified_signals:
                        print(f"  - 导出统一信号 ({len(unified_signals)}条)...")
                        try:
                            if isinstance(unified_signals, dict):
                                # 如果是字典，尝试转换为DataFrame
                                if all(isinstance(v, (list, tuple)) and len(v) == len(list(unified_signals.values())[0]) for v in unified_signals.values()):
                                    # 所有值都是相同长度的列表/元组
                                    unified_df = pd.DataFrame(unified_signals)
                                else:
                                    # 值长度不同或包含标量，转换为键值对格式
                                    unified_df = pd.DataFrame([
                                        {'键': k, '值': str(v)} for k, v in unified_signals.items()
                                    ])
                            elif isinstance(unified_signals, list) and len(unified_signals) > 0:
                                if isinstance(unified_signals[0], dict):
                                    unified_df = pd.DataFrame(unified_signals)
                                else:
                                    unified_df = pd.DataFrame({'信号': unified_signals})
                            else:
                                unified_df = pd.DataFrame({'提示': ['无统一信号']})
                        except Exception as e:
                            print(f"    警告：统一信号DataFrame创建失败: {e}")
                            # 创建调试信息表
                            unified_df = pd.DataFrame({
                                '调试信息': [f'统一信号类型: {type(unified_signals)}', 
                                           f'统一信号内容: {str(unified_signals)[:200]}...']
                            })
                        unified_df.to_excel(writer, sheet_name='统一信号', index=False)
                    else:
                        # 创建空的统一信号表
                        empty_df = pd.DataFrame({'提示': ['无统一信号']})
                        empty_df.to_excel(writer, sheet_name='统一信号', index=False)
                else:
                    # 创建空的统一信号表
                    empty_df = pd.DataFrame({'提示': ['无统一信号']})
                    empty_df.to_excel(writer, sheet_name='统一信号', index=False)
                
                # 5.5 导出汇总信息
                summary_data = {
                    '项目': ['股票代码', '数据时间范围', '股票数据行数', '模拟事件数量', 
                            '数据信号数量', '事件信号数量', '统一信号数量', '导出时间'],
                    '值': [
                        '000001.SH',
                        f"{df['日期'].min()} ~ {df['日期'].max()}",
                        len(df),
                        len(events_data),
                        data_only_result.get('data', {}).get('data_signals_count', 0),
                        data_only_result.get('data', {}).get('event_signals_count', 0),
                        data_only_result.get('data', {}).get('total_signals', 0),
                        timestamp
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
                
            print(f"✓ Excel文件已保存: {excel_file}")
            print(f"  包含工作表: 股票历史数据, 数据信号, 事件信号, 统一信号, 汇总信息")
            
        except Exception as e:
            print(f"❌ Excel导出失败: {e}")
            import traceback
            traceback.print_exc()
        print("\n=== 统一信号生成器调试完成 ===")
        
    except Exception as e:
        logger.error(f"统一信号调试过程中发生错误: {e}")
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_unified_signals()
    # debug_basic_strategy_flow()