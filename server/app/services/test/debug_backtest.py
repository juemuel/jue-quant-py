from app.services.strategy.strategy_service import simple_backtest
from debug_strategy import debug_basic_strategy_flow

def debug_simple_backtest():
    """
    调试简单回测流程
    """
    print("=== 开始调试简单回测 ===")
    
    # 1. 获取基础数据和信号
    basic_results = debug_basic_strategy_flow()
    
    if basic_results['ma_signal']['status'] == 'success':
        # 2. 执行MA交叉策略回测
        print("\n=== MA交叉策略回测 ===")
        ma_backtest = simple_backtest(
            signals_data=basic_results['ma_signal']['data'],
            initial_capital=100000,
            commission_rate=0.001
        )
        
        if ma_backtest['status'] == 'success':
            result = ma_backtest['data']
            print(f"初始资金: {result['initial_capital']:,.2f}")
            print(f"最终价值: {result['final_value']:,.2f}")
            print(f"总收益率: {result['total_return_pct']:.2f}%")
            print(f"交易次数: {result['trades_count']}")
            print(f"完成交易: {result['completed_trades']}")
        else:
            print(f"MA回测失败: {ma_backtest['message']}")
    
    if basic_results['rsi_signal']['status'] == 'success':
        # 3. 执行RSI策略回测
        print("\n=== RSI策略回测 ===")
        rsi_backtest = simple_backtest(
            signals_data=basic_results['rsi_signal']['data'],
            initial_capital=100000,
            commission_rate=0.001
        )
        
        if rsi_backtest['status'] == 'success':
            result = rsi_backtest['data']
            print(f"初始资金: {result['initial_capital']:,.2f}")
            print(f"最终价值: {result['final_value']:,.2f}")
            print(f"总收益率: {result['total_return_pct']:.2f}%")
            print(f"交易次数: {result['trades_count']}")
            print(f"完成交易: {result['completed_trades']}")
        else:
            print(f"RSI回测失败: {rsi_backtest['message']}")

if __name__ == "__main__":
    debug_simple_backtest()