import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from app.services.strategy.backtest_service import EnhancedBacktestService, BacktestConfig, TradingCost
from app.services.test.debug_strategy import debug_unified_signals, get_and_preprocess_stock_data
from app.services.strategy.strategy_service import generate_unified_signals_with_configs
from app.services.storage.excel_storage_service import excel_storage
from app.services.test.debug_strategy import create_mock_events_data, analyze_unified_signals
from app.services.events.event_service import MarketEvent, EventType, EventSeverity
import pandas as pd
import datetime
from core.logger import logger
from common.debug_utils import create_debug_logger, debug_signals, debug_strategy, debug_backtest, debug_data_provider, debug_event_provider

def debug_backtest_system():
    """
    调试回测系统
    """
    # 创建调试日志管理器
    logger = create_debug_logger("调试回测系统功能", "backtest")
    logger.start_session("调试回测系统功能", "测试统一信号生成和回测执行")
    try:
        # 1. 数据获取（此处用了函数默认值）
        logger.step_start("1. 数据获取", "获取和预处理股票数据")
        success, df, message = get_and_preprocess_stock_data()
        if not success:
            logger.step_error("数据获取失败", message)
            return
        logger.step_success("数据获取", f"获取 {len(df)} 行数据", {
            'data_rows': len(df),
            'date_range': f"{df['日期'].min()} ~ {df['日期'].max()}"
        })
        data_df = df.copy()
        # 格式化日期并设为索引
        if '日期' in data_df.columns:
            data_df['日期'] = pd.to_datetime(data_df['日期'])
            data_df = data_df.set_index('日期')
        
        # 2. 信号配置
        logger.step_start("2. 信号配置", "创建数据信号和事件信号配置")
        data_signal_config = {
            'ma_crossover': {
                'enable': True,
                'use_parameterized': True,
                'short_period': 5,
                'long_period': 20,
                'adaptive': True,
                'filter_config': {
                    'volatility_filter': {'enable': True, 'min_volatility': 0.3, 'max_volatility': 1},
                    'volume_confirmation': {'enable': False, 'volume_multiplier': 1, 'lookback_days': 20},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            },
            'rsi': {
                'enable': True,
                'use_parameterized': True,
                'period': 14,
                'oversold': 30,
                'overbought': 70,
                'adaptive': True,
                'filter_config': {
                    'volume_confirmation': {'enable': True, 'volume_multiplier': 1, 'lookback_days': 20},
                    'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 0.5},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            }
        }
        event_signal_config = {
            'news_sentiment': {
                'enable': False,
                'use_parameterized': True,
                'sentiment_threshold': 0.8,
                'severity_levels': [EventSeverity.HIGH, EventSeverity.CRITICAL]
            },
            'earnings': {
                'enable': False,
                'use_parameterized': False
            },
            'keyword_trigger': {
                'enable': False,
                'use_parameterized': True,
                'positive_keywords': ['突破', '创新高', '利好'],
                'negative_keywords': ['暴跌', '亏损', '风险'],
                'strength': 0.7,
            }
        }
        config_details = {
            '数据信号规则': {
                '规则数量': len([k for k, v in data_signal_config.items() if v.get('enable', False)]),
                '启用规则': [k for k, v in data_signal_config.items() if v.get('enable', False)]
            },
            '事件信号规则': {
                '规则数量': len([k for k, v in event_signal_config.items() if v.get('enable', False)]),
                '启用规则': [k for k, v in event_signal_config.items() if v.get('enable', False)]
            }
        }
        logger.step_success("信号配置", "信号配置创建完成", config_details)
         # 3. 事件获取
        logger.step_start("3. 事件获取", "创建模拟事件数据")
        # 检查是否有启用的事件信号规则
        enabled_event_rules = [k for k, v in event_signal_config.items() if v.get('enable', False)]
        has_enabled_events = len(enabled_event_rules) > 0
        events_data = None
        if has_enabled_events:
            events_result = create_mock_events_data(
                df,
                event_count=300
            )
            if not events_result['success']:
                logger.step_error("事件获取", events_result['message'])
                return
            events_data = events_result['data']
            logger.step_success("事件获取", events_result['message'], {
                'events_generated': len(events_data),
                'enabled_rules': enabled_event_rules,
                'time_range': {
                    'start': events_data[0].timestamp.strftime('%Y-%m-%d'),
                    'end': events_data[-1].timestamp.strftime('%Y-%m-%d')
                }
            })
        else:
            logger.step_skip("生成模拟事件", "事件信号规则未启用，跳过事件数据生成")
        # 4. 信号生成
        logger.step_start("4. 信号生成", "生成统一信号")
        unified_result = generate_unified_signals_with_configs(
            price_data=df,
            events_data=events_data,  # 不提供事件数据
            data_signal_config=data_signal_config,
            event_signal_config=event_signal_config 
        )
        debug_signals(analyze_unified_signals(unified_result))
        unified_signals = unified_result.get('data', {}).get('unified_signals')
        if unified_signals is None or len(unified_signals) == 0:
            print("❌ 没有生成有效的统一信号")
            return
        
        signals_df = pd.DataFrame(unified_signals)
        # 确保信号数据中的timestamp也是datetime格式
        if 'timestamp' in signals_df.columns:
            signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])

        # 为回测做字段处理
        if 'direction' in signals_df.columns and 'action' not in signals_df.columns:
            # 数字到action的映射
            direction_to_action = {
                1: 'buy',    # 买入
                -1: 'sell',  # 卖出
                0: 'hold'    # 观望（但回测系统会忽略这个）
            }
            signals_df['action'] = signals_df['direction'].map(direction_to_action)
            
            debug_signals("direction字段分布", {
                "direction值分布": signals_df['direction'].value_counts().to_dict()
            })
            debug_signals("action字段转换", {
                "action字段值分布": signals_df['action'].value_counts().to_dict()
            })
            valid_signals = signals_df[signals_df['action'].isin(['buy', 'sell'])]
            debug_signals("有效交易信号", {
                "过滤前信号数量": len(signals_df),
                "过滤后信号数量": len(valid_signals)
            })
            signals_df = valid_signals
        if 'strength' in signals_df.columns:
            signals_df['strength'] = signals_df['strength'].apply(lambda x: max(0.1, abs(x)))

        if not signals_df.empty:
            signal_dates = set(signals_df['timestamp'].dt.date)
            price_dates = set(data_df.index.date if hasattr(data_df.index[0], 'date') else data_df.index)
            overlapping_dates = signal_dates.intersection(price_dates)
            debug_signals("日期重叠调试", {
                "信号日期数量": len(signal_dates),
                "信号日期类型": type(signal_dates),
                "信号日期范围": f"{min(signal_dates)} 到 {max(signal_dates)}",
                "信号日期样例": list(signal_dates)[:5] if len(signal_dates) > 0 else "无",
                "价格日期数量": len(price_dates),
                "价格日期类型": type(df.index[0]).__name__ if len(price_dates) > 0 else "无",
                "价格日期范围": f"{min(price_dates)} ~ {max(price_dates)}",
                "价格日期样例": list(price_dates)[:5] if len(price_dates) > 0 else "无",
                "重叠日期数量": len(overlapping_dates),
                "重叠日期样例": list(overlapping_dates)[:5] if len(overlapping_dates) > 0 else "无"
            }, level="INFO", horizontal_output=True, show_full_content=True)

        # 转换回字典列表格式
        unified_signals = signals_df.to_dict('records')
        logger.step_info("回测信号数量：", len(unified_signals))

        # 5. 回测配置
        logger.step_start("5. 回测配置", "配置回测参数")
        # 配置回测参数
        backtest_config = BacktestConfig(
            initial_capital=1000000.0,
            max_position_size=0.80,
            trading_cost=TradingCost(
                commission_rate=0.0003,
                min_commission=5.0,
                stamp_tax_rate=0.001,
                transfer_fee_rate=0.00002
            )
        )
        config_info = {
            '初始资金': f"{backtest_config.initial_capital:,.0f} 元",
            '最大仓位': f"{backtest_config.max_position_size*100:.1f}%",
            # 移除最小交易金额的显示
            '交易成本': {
                '佣金费率': f"{backtest_config.trading_cost.commission_rate*10000:.1f} 万分之一",
                '最小佣金': f"{backtest_config.trading_cost.min_commission:.0f} 元",
                '印花税': f"{backtest_config.trading_cost.stamp_tax_rate*1000:.1f} 千分之一",
                '过户费': f"{backtest_config.trading_cost.transfer_fee_rate*100000:.1f} 十万分之一"
            }
        }
        logger.step_success("回测配置", "回测参数配置完成", config_info)
        
        # 6. 执行回测
        logger.step_start("6. 回测执行", "执行回测计算")
        debug_signals("回测用的价格数据调试", {
            "价格数据形状": data_df.shape,
            "价格数据列名": list(data_df.columns),
            "价格数据样例": data_df.head() if not data_df.empty else "无数据"
        }, level="INFO", horizontal_output=True, show_full_content=True)
        debug_signals("回测用的信号数据调试", {
            "信号数据形状": signals_df.shape,
            "信号数据列名": list(signals_df.columns),
            "信号数据样例": signals_df.head() if not signals_df.empty else "无数据"
        }, level="INFO", horizontal_output=True, show_full_content=True)
        backtest_service = EnhancedBacktestService(config=backtest_config)
        backtest_result = backtest_service.realistic_backtest(
            price_data=data_df,
            signals=unified_signals
        )
        if not backtest_result.get('success', False):
            logger.step_error("回测执行失败", backtest_result.get('message', '未知错误'))
            return
       
         # 分析回测结果
        performance = backtest_result.get('data', {}).get('performance', {})
        trades = backtest_result.get('data', {}).get('trades', [])
        
        backtest_stats = {
            '回测结果': {
                '总收益率': f"{performance.get('total_return', 0)*100:.2f}%",
                '年化收益率': f"{performance.get('annualized_return', 0)*100:.2f}%",
                '最大回撤': f"{performance.get('max_drawdown', 0)*100:.2f}%",
                '夏普比率': f"{performance.get('sharpe_ratio', 0):.3f}"
            },
            '交易统计': {
                '总交易次数': len(trades),
                '盈利交易': len([t for t in trades if t.get('pnl', 0) > 0]),
                '亏损交易': len([t for t in trades if t.get('pnl', 0) < 0]),
                '胜率': f"{len([t for t in trades if t.get('pnl', 0) > 0])/max(1, len(trades))*100:.1f}%" if trades else "0%"
            }
        }
        logger.step_success("回测执行", "回测计算完成", backtest_stats)
        
        # 7. 结果分析与导出
        logger.step_start("7. 结果分析", "分析回测结果并输出详细信息")
        
        # 7.1 输出详细的回测分析结果
        print("\n=== 回测结果摘要 ===")
        performance = backtest_result.get('data', {}).get('performance', {})
        trades = backtest_result.get('data', {}).get('trades', [])
        
        # 基本性能指标
        print(f"总收益率: {performance.get('total_return', 0)*100:.2f}%")
        print(f"年化收益率: {performance.get('annualized_return', 0)*100:.2f}%")
        print(f"年化波动率: {performance.get('volatility', 0)*100:.2f}%")
        print(f"夏普比率: {performance.get('sharpe_ratio', 0):.2f}")
        print(f"最大回撤: {performance.get('max_drawdown', 0)*100:.2f}%")
        
        # 交易统计
        print(f"\n=== 交易统计 ===")
        profitable_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades if t.get('pnl', 0) < 0])
        total_trades = len(trades)
        
        if total_trades > 0:
            win_rate = profitable_trades / total_trades
            avg_win = sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]) / max(1, profitable_trades)
            avg_loss = sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]) / max(1, losing_trades)
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            total_trading_costs = sum([t.get('cost', 0) for t in trades])
            
            print(f"总交易次数: {total_trades}")
            print(f"盈利交易次数: {profitable_trades}")
            print(f"亏损交易次数: {losing_trades}")
            print(f"胜率: {win_rate:.2%}")
            print(f"平均盈利: {avg_win:.2f}%")
            print(f"平均亏损: {avg_loss:.2f}%")
            print(f"盈亏比: {profit_factor:.2f}")
            print(f"总交易成本: {total_trading_costs:.2f}")
            print(f"初始资产: {backtest_config.initial_capital:.2f}")
            print(f"最终资产: {performance.get('final_value', backtest_config.initial_capital):.2f}")
        else:
            print("没有执行任何交易")
        
        # 基准对比（如果有）
        benchmark_metrics = performance.get('benchmark_metrics', {})
        if benchmark_metrics:
            print(f"\n=== 基准对比 ===")
            print(f"基准收益率: {benchmark_metrics.get('benchmark_return', 0):.2%}")
            print(f"超额收益: {benchmark_metrics.get('excess_return', 0):.2%}")
            print(f"Alpha: {benchmark_metrics.get('alpha', 0):.2%}")
            print(f"Beta: {benchmark_metrics.get('beta', 0):.2f}")
        
        # 记录分析结果到日志
        analysis_stats = {
            '性能指标': {
                '总收益率': f"{performance.get('total_return', 0)*100:.2f}%",
                '年化收益率': f"{performance.get('annualized_return', 0)*100:.2f}%",
                '最大回撤': f"{performance.get('max_drawdown', 0)*100:.2f}%",
                '夏普比率': f"{performance.get('sharpe_ratio', 0):.3f}"
            },
            '交易统计': {
                '总交易次数': total_trades,
                '盈利交易': profitable_trades,
                '亏损交易': losing_trades,
                '胜率': f"{win_rate*100:.1f}%" if total_trades > 0 else "0%"
            }
        }
        logger.step_success("结果分析", "回测结果分析完成", analysis_stats)


        # 7.2 导出到Excel
        logger.step_start("8. 结果导出", "导出回测结果到Excel")
        
        try:
            # 创建汇总信息
            summary_info = {
                '项目': ['股票代码', '数据时间范围', '股票数据行数', '统一信号数量', 
                        '总收益率', '年化收益率', '最大回撤', '夏普比率', '总交易次数', '胜率', '导出时间'],
                '值': [
                    '000001.SH',
                    f"{df['日期'].min()} ~ {df['日期'].max()}",
                    len(df),
                    len(unified_signals),
                    f"{performance.get('total_return', 0)*100:.2f}%",
                    f"{performance.get('annualized_return', 0)*100:.2f}%",
                    f"{performance.get('max_drawdown', 0)*100:.2f}%",
                    f"{performance.get('sharpe_ratio', 0):.3f}",
                    total_trades,
                    f"{win_rate*100:.1f}%" if total_trades > 0 else "0%",
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            
            excel_file = excel_storage.save_backtest_results(
                stock_data=df,
                signals=unified_signals,
                trades=trades,
                performance=performance,
                summary_info=summary_info,
                filename_prefix="backtest_debug"
            )
            
            print(f"\n✓ Excel文件已保存: {excel_file}")
            print(f"  包含工作表: 股票历史数据, 统一信号, 交易记录, 回测表现, 汇总信息")
            
            export_info = {
                '文件路径': excel_file,
                '包含工作表': ['股票历史数据', '统一信号', '交易记录', '回测表现', '汇总信息']
            }
            logger.step_success("结果导出", "Excel文件导出完成", export_info)
            
        except Exception as e:
            logger.step_error("结果导出失败", str(e))
            print(f"❌ Excel导出失败: {e}")
            
        logger.end_session("回测调试完成")
        
    except Exception as e:
        logger.error(f"回测系统测试失败: {e}")
        print(f"❌ 回测系统测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_backtest_system()