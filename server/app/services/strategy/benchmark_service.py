class BenchmarkService:
    """基准对比服务"""
    
    def __init__(self):
        self.benchmark_data = {}
    
    def load_benchmark_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载基准数据
        """
        # 这里可以调用你现有的数据服务
        from app.services.data.data_service import get_stock_data
        
        benchmark_data = get_stock_data(symbol, start_date, end_date)
        self.benchmark_data[symbol] = benchmark_data
        return benchmark_data
    
    def compare_with_benchmark(self, strategy_returns: List[float], 
                             benchmark_symbol: str = '000300.SH') -> Dict:
        """
        与基准进行详细对比
        """
        if benchmark_symbol not in self.benchmark_data:
            return {'error': f'基准数据 {benchmark_symbol} 未加载'}
        
        benchmark_data = self.benchmark_data[benchmark_symbol]
        benchmark_returns = benchmark_data['close'].pct_change().dropna().tolist()
        
        # 计算相对性能指标
        comparison_metrics = self._calculate_comparison_metrics(
            strategy_returns, benchmark_returns
        )
        
        return comparison_metrics