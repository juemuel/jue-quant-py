import logging
from core.logger import logger
from data_providers import get_data_provider
data_provider = get_data_provider('yfinance')  # 使用 yfinance 数据源
# 关闭 FastAPI/Uvicorn 自带 logging 输出干扰
logging.getLogger('uvicorn').handlers = []

@logger.catch
def get_concept_board_top10(top_n=10, filter_by=None):
    """
    获取概念板块排名（带参数支持）
    :param top_n: 返回前 N 名
    :param filter_by: 可选筛选条件
    :return: DataFrame
    """
    logger.info(f"Fetching top {top_n} concept boards")
    df = data_provider.get_concept_board_top10()

    if filter_by:
        # 示例：filter_by = {'涨幅': 5}
        for col, value in filter_by.items():
            df = df[df[col] > value]

    return df.head(top_n)
