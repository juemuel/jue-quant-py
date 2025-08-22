import sys
sys.path.append('../../..')

from app.services.portfolio.portfolio_service import PortfolioService

def test_portfolio_basic_operations():
    """测试基本的投资组合操作"""
    print("=== Portfolio服务基础功能测试 ===")
    
    # 创建投资组合
    portfolio_service = PortfolioService(initial_capital=100000)
    
    print(f"初始资金: {portfolio_service.portfolio.cash}")
    
    # 买入股票
    success = portfolio_service.buy_stock('000001.SZ', 1000, 10.5, trading_cost=10.5)
    print(f"买入结果: {success}")
    
    # 更新价格
    portfolio_service.update_prices({'000001.SZ': 11.0})
    
    # 获取组合摘要
    summary = portfolio_service.get_portfolio_summary()
    print(f"\n组合摘要:")
    for key, value in summary.items():
        if key != 'positions':
            print(f"  {key}: {value}")
    
    print(f"\n持仓详情:")
    for symbol, pos in summary['positions'].items():
        print(f"  {symbol}: {pos}")
    
    # 部分卖出
    success = portfolio_service.sell_stock('000001.SZ', 500, 11.2, trading_cost=5.6)
    print(f"\n卖出结果: {success}")
    
    # 最终摘要
    final_summary = portfolio_service.get_portfolio_summary()
    print(f"\n最终组合价值: {final_summary['total_value']}")
    print(f"总盈亏: {final_summary['total_pnl']}")
    
    # 交易历史
    trades = portfolio_service.get_trade_history()
    print(f"\n交易历史:")
    for trade in trades:
        print(f"  {trade}")

if __name__ == '__main__':
    test_portfolio_basic_operations()