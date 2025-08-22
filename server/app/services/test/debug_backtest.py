import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from app.services.strategy.backtest_service import EnhancedBacktestService, BacktestConfig, TradingCost
from app.services.test.debug_strategy import debug_unified_signals, get_and_preprocess_stock_data
from app.services.strategy.strategy_service import generate_unified_signals
from app.services.storage.excel_storage_service import excel_storage
import pandas as pd
import datetime
from core.logger import logger

def debug_backtest_system():
    try:
        print("=== 开始测试回测系统 ===")
        
        # 1. 直接调用debug_unified_signals获取信号数据
        print("\n1. 生成统一信号（使用debug_strategy方法）...")
        
        # 临时重定向debug_unified_signals的输出，获取其生成的信号数据
        # 由于debug_unified_signals主要用于调试输出，我们需要修改策略
        
        # 方案1：直接获取数据和信号
        success, df, message = get_and_preprocess_stock_data(
            source="akshare",
            code="000001", 
            market="SH",
            start_date="20240301",
            end_date="20241201"
        )
        
        if not success:
            print(f"❌ 数据获取失败: {message}")
            return
            
        print(f"✓ {message}")
        
        # 使用与debug_unified_signals相同的配置生成信号
        from app.services.test.debug_strategy import create_mock_events_data
        
        events_data = create_mock_events_data(df, event_count=50)
        print(f"✓ 创建了 {len(events_data)} 个模拟事件")
        
        # 使用debug_strategy中相同的配置
        data_signal_config = {
            'ma_crossover': {
                'enable': True,
                'use_parameterized': False,
                'short_period': 5,
                'long_period': 20,
                'adaptive': True,
                'filter_config': {
                    'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 1},
                    'volume_confirmation': {'enable': False, 'volume_multiplier': 1, 'lookback_days': 20},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            },
            'rsi': {
                'enable': True,
                'use_parameterized': False,
                'period': 14,
                'oversold': 30,
                'overbought': 70,
                'adaptive': True,
                'filter_config': {
                    'volume_confirmation': {'enable': False, 'volume_multiplier': 1, 'lookback_days': 20},
                    'volatility_filter': {'enable': False, 'min_volatility': 0.3, 'max_volatility': 0.5},
                    'trend_strength_filter': {'enable': False, 'min_adx': 25},
                    'signal_strength_filter': {'enable': False, 'min_strength': 0.3}
                }
            }
        }
        
        # 注意：使用price_data参数而不是df
        data_only_result = generate_unified_signals(
            price_data=df,  # 使用price_data参数
            events_data=None,
            data_signal_config=data_signal_config,
            event_signal_config=None
        )
        
        if data_only_result.get('status') != 'success':
            print(f"❌ 信号生成失败: {data_only_result.get('message')}")
            return
            
        signals_data = data_only_result.get('data', {})
        unified_signals = signals_data.get('unified_signals')
        
        if unified_signals is None or len(unified_signals) == 0:
            print("❌ 没有生成有效的统一信号")
            return
            
        signals_df = pd.DataFrame(unified_signals)
        print(f"✓ 生成了 {len(signals_df)} 条信号记录")
        
    

        # 2. 配置回测参数
        print("\n2. 配置回测参数...")
        trading_cost = TradingCost(
            commission_rate=0.0003,
            stamp_tax_rate=0.001,
            min_commission=5.0,
            slippage_rate=0.001
        )
        
        config = BacktestConfig(
            initial_capital=1000000,
            trading_cost=trading_cost,
            max_position_size=0.95,
            benchmark_symbol="000300.SH"
        )
        
        # 3. 执行回测
        print("\n3. 执行回测...")
        
        # 添加调试信息
        print(f"\n=== 调试信息 ===")
        print(f"价格数据形状: {df.shape}")
        print(f"价格数据列: {list(df.columns)}")
        print(f"信号数量: {len(signals_df)}")
        print(f"信号列: {list(signals_df.columns)}")
        
        print(f"价格数据日期范围: {df['日期'].min()} 到 {df['日期'].max()}")
        
        # 检查信号强度分布
        if 'signal_strength' in signals_df.columns:
            strength_stats = signals_df['signal_strength'].describe()
            print(f"信号强度统计: \n{strength_stats}")

        # 添加日期匹配调试
        print(f"\n=== 日期匹配调试 ===")
        
        # 准备数据用于调试
        price_data_for_debug = df.set_index('日期')
        signals_list_for_debug = signals_df.to_dict('records')
        
        price_dates = price_data_for_debug.index.tolist()
        signal_dates = [pd.to_datetime(s['timestamp']).date() for s in signals_list_for_debug]
        
        print(f"价格数据日期示例: {price_dates[:5]}")
        print(f"价格数据日期类型: {type(price_dates[0])}")
        print(f"信号日期示例: {signal_dates[:5]}")
        print(f"信号日期类型: {type(signal_dates[0])}")
        
        # 检查日期重叠
        price_date_set = set([d.date() if hasattr(d, 'date') else pd.to_datetime(d).date() for d in price_dates])
        signal_date_set = set(signal_dates)
        overlap = price_date_set.intersection(signal_date_set)
        print(f"重叠日期数量: {len(overlap)}")
        if overlap:
            print(f"重叠日期示例: {list(overlap)[:5]}")
        else:
            print("❌ 没有重叠日期！这就是为什么没有执行交易的原因")
            print(f"价格日期范围: {min(price_date_set)} 到 {max(price_date_set)}")
            print(f"信号日期范围: {min(signal_date_set)} 到 {max(signal_date_set)}")


        # 创建回测服务时传入配置
        backtest_service = EnhancedBacktestService(config=config)
         # 准备数据：将日期设为索引
        price_data_indexed = df.set_index('日期')
        
        # 将signals_df转换为字典列表
        signals_list = signals_df.to_dict('records')
                # 转换信号格式以匹配回测服务的期望
        print(f"\n=== 信号格式转换 ===")
        converted_signals = []
        for signal in signals_list:
            # 检查原始信号格式
            if len(converted_signals) < 3:  # 只打印前3个原始信号
                print(f"原始信号: {signal}")
            
            # 获取信号强度，确保有合理的最小值
            original_strength = signal.get('strength', signal.get('signal_strength', 0.5))
            # 如果信号强度太小，设置一个最小值
            adjusted_strength = max(abs(original_strength), 0.1)  # 最小10%的仓位
            
            # 转换为回测服务期望的格式
            converted_signal = {
                'symbol': signal.get('symbol', '000001.SH'),
                'action': signal.get('signal_type', 'buy'),  # 直接使用signal_type
                'strength': adjusted_strength,
                'timestamp': signal.get('timestamp')
            }
            
            # 确保action字段正确
            if converted_signal['action'] not in ['buy', 'sell']:
                # 根据direction判断
                direction = signal.get('direction', 1)
                converted_signal['action'] = 'buy' if direction > 0 else 'sell'
            
            converted_signals.append(converted_signal)
            
            if len(converted_signals) <= 3:  # 只打印前3个转换后的信号
                print(f"转换后信号: {converted_signal}")
        
        print(f"转换完成，共{len(converted_signals)}个信号")
        print(f"信号强度调整: 原始范围可能很小，已调整为最小0.1")
        # 统计信号类型
        buy_signals = [s for s in converted_signals if s['action'] == 'buy']
        sell_signals = [s for s in converted_signals if s['action'] == 'sell']
        print(f"买入信号数量: {len(buy_signals)}")
        print(f"卖出信号数量: {len(sell_signals)}")
        if buy_signals:
            print(f"买入信号示例: {buy_signals[0]}")

        # 使用转换后的信号
        signals_list = converted_signals
        
        # 添加回测前的最终检查
        print(f"\n=== 回测前最终检查 ===")
        print(f"价格数据索引类型: {type(price_data_indexed.index[0])}")
        print(f"价格数据列名: {list(price_data_indexed.columns)}")
        print(f"信号列表长度: {len(signals_list)}")
        
        # 检查价格数据是否包含必要的列
        required_columns = ['close', '收盘价']
        available_columns = [col for col in required_columns if col in price_data_indexed.columns]
        print(f"可用的价格列: {available_columns}")
        
        if not available_columns:
            print(f"❌ 错误：价格数据中缺少收盘价列！")
            print(f"当前列名: {list(price_data_indexed.columns)}")
            return
        
        # 检查几个具体日期的信号和价格匹配
        print(f"\n=== 具体日期检查 ===")
        for i, signal in enumerate(signals_list[:3]):
            signal_date = pd.to_datetime(signal['timestamp']).date()
            print(f"\n信号 {i+1}:")
            print(f"  日期: {signal_date}")
            print(f"  动作: {signal['action']}")
            print(f"  强度: {signal['strength']}")
            print(f"  股票: {signal['symbol']}")
            
            # 检查该日期是否在价格数据中
            matching_dates = [d for d in price_data_indexed.index if d.date() == signal_date]
            if matching_dates:
                price_date = matching_dates[0]
                price_row = price_data_indexed.loc[price_date]
                close_price = price_row.get('close', price_row.get('收盘价', 0))
                print(f"  匹配价格日期: {price_date}")
                print(f"  收盘价: {close_price}")
            else:
                print(f"  ❌ 该日期在价格数据中不存在")
        
        # 检查配置
        print(f"\n=== 配置检查 ===")
        print(f"初始资金: {config.initial_capital}")
        print(f"最大仓位: {config.max_position_size}")
        print(f"手续费率: {config.trading_cost.commission_rate}")

        # # 回测调用：realistic_backtest
        backtest_result = backtest_service.realistic_backtest(
            price_data=price_data_indexed,
            signals=signals_list
        )
        
        if backtest_result.get('status') != 'success':
            print(f"❌ 回测执行失败: {backtest_result.get('message')}")
            return
        
        # # 4. 分析回测结果
        print("\n4. 分析回测结果...")
        if backtest_result['status'] == 'success':
            result_data = backtest_result['data']
            performance_metrics = result_data['performance_metrics']
            
            print("\n=== 回测结果摘要 ===")
            print(f"总收益率: {performance_metrics['total_return']:.2%}")
            print(f"年化收益率: {performance_metrics['annual_return']:.2%}")
            print(f"年化波动率: {performance_metrics['volatility']:.2%}")
            print(f"夏普比率: {performance_metrics['sharpe_ratio']:.2f}")
            print(f"最大回撤: {performance_metrics['max_drawdown']:.2%}")
            
        #     # 交易统计
            trade_stats = performance_metrics.get('trade_statistics', {})
            print(f"\n=== 交易统计 ===")
            if trade_stats:
                print(f"总交易次数: {trade_stats.get('total_trades', 0)}")
                print(f"盈利交易次数: {trade_stats.get('profitable_trades', 0)}")
                print(f"亏损交易次数: {trade_stats.get('losing_trades', 0)}")
                print(f"胜率: {trade_stats.get('win_rate', 0):.2%}")
                print(f"平均盈利: {trade_stats.get('avg_win', 0):.2f}%")
                print(f"平均亏损: {trade_stats.get('avg_loss', 0):.2f}%")
                print(f"盈亏比: {trade_stats.get('profit_factor', 0):.2f}")
                print(f"总交易成本: {trade_stats.get('total_trading_costs', 0):.2f}")
            else:
                print("没有执行任何交易")
            
            # 基准对比（如果有）
            benchmark_metrics = performance_metrics['benchmark_metrics']
            if benchmark_metrics:
                print(f"\n=== 基准对比 ===")
                print(f"基准收益率: {benchmark_metrics['benchmark_return']:.2%}")
                print(f"超额收益: {benchmark_metrics['excess_return']:.2%}")
                print(f"Alpha: {benchmark_metrics['alpha']:.2%}")
                print(f"Beta: {benchmark_metrics['beta']:.2f}")
        
        # 5. 导出回测结果
        print("\n5. 导出回测结果...")
        try:
            # 使用新的专门方法导出回测结果
            filename = excel_storage.save_backtest_results(
                backtest_result=backtest_result,
                config=config,
                signals_data=signals_list,
                price_data=price_data_indexed,
                filename_prefix="backtest_results"
            )
            print(f"✓ 回测结果已导出到: {filename}")
            
        except Exception as e:
            logger.error(f"导出回测结果失败: {e}")
            print(f"❌ 导出失败: {e}")
        
        print("\n=== 回测系统测试完成 ===")
        
    except Exception as e:
        logger.error(f"回测系统测试失败: {e}")
        print(f"❌ 回测系统测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_backtest_system()