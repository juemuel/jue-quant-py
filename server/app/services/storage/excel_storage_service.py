import os
import pandas as pd
import datetime
from typing import Dict, List, Any, Optional, Union
from core.logger import logger
import openpyxl

class ExcelStorageService:
    """
    Excel文档存储服务
    用于统一管理策略数据的Excel导出功能
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化Excel存储服务
        
        Args:
            base_dir: 基础保存目录，默认为项目根目录下的logs文件夹
        """
        if base_dir is None:
            # 获取项目根目录 - 修正路径计算
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 从 server/app/services/ 向上3级到达项目根目录 jue-quant-py/
            project_root = os.path.join(current_dir, '../../..')
            # 规范化路径
            project_root = os.path.normpath(project_root)
            self.base_dir = os.path.join(project_root, 'logs')
        else:
            self.base_dir = base_dir
            
        # 确保logs目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Excel存储服务初始化，保存目录: {self.base_dir}")
    
    def _generate_filename(self, prefix: str, suffix: str = "") -> str:
        """
        生成带时间戳的文件名
        
        Args:
            prefix: 文件名前缀
            suffix: 文件名后缀
            
        Returns:
            完整的文件路径
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}{suffix}.xlsx"
        return os.path.join(self.base_dir, filename)
    
    def _safe_dataframe_conversion(self, data: Any, fallback_name: str = "数据") -> pd.DataFrame:
        """
        安全地将数据转换为DataFrame
        
        Args:
            data: 要转换的数据
            fallback_name: 转换失败时的列名
            
        Returns:
            转换后的DataFrame
        """
        try:
            if data is None or (isinstance(data, (list, tuple)) and len(data) == 0):
                return pd.DataFrame({'提示': [f'无{fallback_name}']})
            
            if isinstance(data, pd.DataFrame):
                return data
            
            if isinstance(data, dict):
                # 检查是否所有值都是相同长度的列表
                if all(isinstance(v, (list, tuple)) and len(v) == len(list(data.values())[0]) for v in data.values()):
                    return pd.DataFrame(data)
                else:
                    # 转换为键值对格式
                    return pd.DataFrame([
                        {'键': k, '值': str(v)} for k, v in data.items()
                    ])
            
            if isinstance(data, (list, tuple)):
                if len(data) > 0 and isinstance(data[0], dict):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame({fallback_name: data})
            
            # 其他类型转换为字符串
            return pd.DataFrame({fallback_name: [str(data)]})
            
        except Exception as e:
            logger.warning(f"数据转换失败: {e}，使用调试信息")
            return pd.DataFrame({
                '调试信息': [
                    f'{fallback_name}类型: {type(data)}',
                    f'{fallback_name}内容: {str(data)[:200]}...'
                ]
            })
    
    def save_basic_strategy_data(self, 
                               ma_signals: List[Dict] = None,
                               rsi_signals: List[Dict] = None,
                               raw_data: pd.DataFrame = None,
                               filename_prefix: str = "basic_strategy_signals") -> str:
        """
        保存基础策略数据到Excel
        
        Args:
            ma_signals: MA交叉信号数据
            rsi_signals: RSI信号数据
            raw_data: 原始股票数据（包含指标）
            filename_prefix: 文件名前缀
            
        Returns:
            保存的文件路径
        """
        excel_file = self._generate_filename(filename_prefix)
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 导出MA信号
                if ma_signals:
                    ma_df = self._safe_dataframe_conversion(ma_signals, "MA信号")
                    ma_df.to_excel(writer, sheet_name='MA_Signals', index=False)
                    logger.info(f"MA信号已导出 ({len(ma_signals)}条)")
                else:
                    empty_df = pd.DataFrame({'提示': ['无MA信号']})
                    empty_df.to_excel(writer, sheet_name='MA_Signals', index=False)
                
                # 导出RSI信号
                if rsi_signals:
                    rsi_df = self._safe_dataframe_conversion(rsi_signals, "RSI信号")
                    rsi_df.to_excel(writer, sheet_name='RSI_Signals', index=False)
                    logger.info(f"RSI信号已导出 ({len(rsi_signals)}条)")
                else:
                    empty_df = pd.DataFrame({'提示': ['无RSI信号']})
                    empty_df.to_excel(writer, sheet_name='RSI_Signals', index=False)
                
                # 导出原始数据
                if raw_data is not None and not raw_data.empty:
                    raw_data.to_excel(writer, sheet_name='Raw_Data', index=False)
                    logger.info(f"原始数据已导出 ({len(raw_data)}行)")
                else:
                    empty_df = pd.DataFrame({'提示': ['无原始数据']})
                    empty_df.to_excel(writer, sheet_name='Raw_Data', index=False)
                
                # 创建汇总信息
                summary_data = {
                    '项目': ['MA信号数量', 'RSI信号数量', '原始数据行数', '导出时间'],
                    '值': [
                        len(ma_signals) if ma_signals else 0,
                        len(rsi_signals) if rsi_signals else 0,
                        len(raw_data) if raw_data is not None else 0,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
            
            logger.info(f"基础策略数据已保存到: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"保存基础策略数据失败: {e}")
            raise
    
    def save_unified_strategy_data(self,
                                 stock_data: pd.DataFrame = None,
                                 data_signals: Any = None,
                                 event_signals: Any = None,
                                 unified_signals: Any = None,
                                 events_data: List = None,
                                 summary_info: Dict = None,
                                 filename_prefix: str = "unified_signals_debug") -> str:
        """
        保存统一策略数据到Excel
        
        Args:
            stock_data: 股票历史数据
            data_signals: 数据驱动信号
            event_signals: 事件驱动信号
            unified_signals: 统一信号
            events_data: 事件数据
            summary_info: 汇总信息
            filename_prefix: 文件名前缀
            
        Returns:
            保存的文件路径
        """
        excel_file = self._generate_filename(filename_prefix)
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 导出股票历史数据
                if stock_data is not None and not stock_data.empty:
                    stock_data.to_excel(writer, sheet_name='股票历史数据', index=False)
                    logger.info(f"股票历史数据已导出 ({len(stock_data)}行)")
                else:
                    empty_df = pd.DataFrame({'提示': ['无股票历史数据']})
                    empty_df.to_excel(writer, sheet_name='股票历史数据', index=False)
                
                # 导出数据信号
                data_signals_df = self._safe_dataframe_conversion(data_signals, "数据信号")
                data_signals_df.to_excel(writer, sheet_name='数据信号', index=False)
                if data_signals:
                    logger.info(f"数据信号已导出 ({len(data_signals) if isinstance(data_signals, (list, tuple)) else '未知数量'}条)")
                
                # 导出事件信号
                event_signals_df = self._safe_dataframe_conversion(event_signals, "事件信号")
                event_signals_df.to_excel(writer, sheet_name='事件信号', index=False)
                if event_signals:
                    logger.info(f"事件信号已导出 ({len(event_signals) if isinstance(event_signals, (list, tuple)) else '未知数量'}条)")
                
                # 导出统一信号
                unified_signals_df = self._safe_dataframe_conversion(unified_signals, "统一信号")
                unified_signals_df.to_excel(writer, sheet_name='统一信号', index=False)
                if unified_signals:
                    logger.info(f"统一信号已导出 ({len(unified_signals) if isinstance(unified_signals, (list, tuple)) else '未知数量'}条)")
                
                # 导出事件数据（如果提供）
                if events_data:
                    events_df = self._safe_dataframe_conversion(events_data, "事件数据")
                    events_df.to_excel(writer, sheet_name='事件数据', index=False)
                    logger.info(f"事件数据已导出 ({len(events_data)}条)")
                
                # 创建汇总信息
                if summary_info:
                    summary_df = self._safe_dataframe_conversion(summary_info, "汇总信息")
                else:
                    # 默认汇总信息
                    summary_data = {
                        '项目': ['股票数据行数', '数据信号数量', '事件信号数量', '统一信号数量', '事件数据数量', '导出时间'],
                        '值': [
                            len(stock_data) if stock_data is not None else 0,
                            len(data_signals) if isinstance(data_signals, (list, tuple)) else 0,
                            len(event_signals) if isinstance(event_signals, (list, tuple)) else 0,
                            len(unified_signals) if isinstance(unified_signals, (list, tuple)) else 0,
                            len(events_data) if events_data else 0,
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                
                summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
            
            logger.info(f"统一策略数据已保存到: {excel_file}")
            logger.info(f"包含工作表: 股票历史数据, 数据信号, 事件信号, 统一信号, 汇总信息")
            return excel_file
            
        except Exception as e:
            logger.error(f"保存统一策略数据失败: {e}")
            raise
    
    def save_backtest_results(self, 
                         backtest_result: Dict[str, Any],
                         config: Any = None,
                         signals_data: List[Dict] = None,
                         price_data: pd.DataFrame = None,
                         filename_prefix: str = "backtest_results") -> str:
        """
        保存回测结果到Excel，将数据分别保存到不同的工作表
        
        Args:
            backtest_result: 回测结果数据
            config: 回测配置
            signals_data: 信号数据
            price_data: 价格数据
            filename_prefix: 文件名前缀
            
        Returns:
            保存的文件路径
        """
        excel_file = self._generate_filename(filename_prefix)
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 1. 回测摘要（核心指标）
                if backtest_result.get('data'):
                    data = backtest_result['data']
                    performance_metrics = data.get('performance_metrics', {})
                    
                    summary_data = {
                        '指标': ['总收益率', '年化收益率', '最大回撤', '夏普比率', '胜率', '总交易次数', '盈利交易次数', '亏损交易次数'],
                        '数值': [
                            f"{performance_metrics.get('total_return', 0):.2%}",
                            f"{performance_metrics.get('annual_return', 0):.2%}",
                            f"{performance_metrics.get('max_drawdown', 0):.2%}",
                            f"{performance_metrics.get('sharpe_ratio', 0):.2f}",
                            f"{performance_metrics.get('win_rate', 0):.2%}",
                            performance_metrics.get('total_trades', 0),
                            performance_metrics.get('profitable_trades', 0),
                            performance_metrics.get('losing_trades', 0)
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='回测摘要', index=False)
                
                # 2. 组合价值历史
                portfolio_history = backtest_result.get('data', {}).get('portfolio_history', [])
                if portfolio_history:
                    portfolio_df = self._safe_dataframe_conversion(portfolio_history, '组合价值历史')
                    portfolio_df.to_excel(writer, sheet_name='组合价值历史', index=False)
                
                # 3. 交易历史
                trades_history = backtest_result.get('data', {}).get('trades_history', [])
                if trades_history:
                    trades_df = self._safe_dataframe_conversion(trades_history, '交易历史')
                    trades_df.to_excel(writer, sheet_name='交易历史', index=False)
                
                # 4. 详细性能指标
                performance_metrics = backtest_result.get('data', {}).get('performance_metrics', {})
                if performance_metrics:
                    perf_df = self._safe_dataframe_conversion(performance_metrics, '性能指标')
                    perf_df.to_excel(writer, sheet_name='性能指标', index=False)
                
                # 5. 回测配置
                if config:
                    config_data = {
                        '配置项': ['初始资金', '手续费率', '印花税率', '过户费率', '最低手续费', '滑点率', '最大仓位', '基准指数'],
                        '数值': [
                            config.initial_capital,
                            config.trading_cost.commission_rate,
                            config.trading_cost.stamp_tax_rate,
                            config.trading_cost.transfer_fee_rate,
                            config.trading_cost.min_commission,
                            config.trading_cost.slippage_rate,
                            config.max_position_size,
                            config.benchmark_symbol or 'N/A'
                        ]
                    }
                    config_df = pd.DataFrame(config_data)
                    config_df.to_excel(writer, sheet_name='回测配置', index=False)
                
                # 6. 交易信号
                if signals_data:
                    signals_df = self._safe_dataframe_conversion(signals_data, '交易信号')
                    signals_df.to_excel(writer, sheet_name='交易信号', index=False)
                
                # 7. 价格数据（可选，数据量大时可能影响性能）
                if price_data is not None and len(price_data) <= 1000:  # 限制行数避免文件过大
                    price_data.to_excel(writer, sheet_name='价格数据', index=False)
                
                logger.info(f"回测结果已保存到: {excel_file}")
                return excel_file
                
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")
            raise
    def save_custom_data(self, 
                        data_dict: Dict[str, Any],
                        filename_prefix: str = "custom_data",
                        include_summary: bool = True) -> str:
        """
        保存自定义数据到Excel
        
        Args:
            data_dict: 数据字典，键为工作表名，值为要保存的数据
            filename_prefix: 文件名前缀
            include_summary: 是否包含汇总信息表
            
        Returns:
            保存的文件路径
        """
        excel_file = self._generate_filename(filename_prefix)
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                sheet_info = []
                
                for sheet_name, data in data_dict.items():
                    df = self._safe_dataframe_conversion(data, sheet_name)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    data_count = len(data) if isinstance(data, (list, tuple, pd.DataFrame)) else 1
                    sheet_info.append({'工作表': sheet_name, '数据量': data_count})
                    logger.info(f"{sheet_name}已导出 ({data_count}条)")
                
                # 添加汇总信息
                if include_summary:
                    summary_data = {
                        '项目': ['工作表数量', '导出时间'] + [info['工作表'] for info in sheet_info],
                        '值': [len(data_dict), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + [info['数据量'] for info in sheet_info]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
            
            logger.info(f"自定义数据已保存到: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"保存自定义数据失败: {e}")
            raise
    
    def get_logs_directory(self) -> str:
        """
        获取logs目录路径
        
        Returns:
            logs目录的绝对路径
        """
        return os.path.abspath(self.base_dir)

# 创建全局实例
excel_storage = ExcelStorageService()