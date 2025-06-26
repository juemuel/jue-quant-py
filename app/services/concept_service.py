# app/services/concept_service.py
from data_source.concept_data import get_concept_board_top10
import logging
logger = logging.getLogger(__name__)
def get_concept_board_top10(top_n=10, filter_by=None):
    """
    获取概念板块排名（带参数支持）
    :param top_n: 返回前 N 名
    :param filter_by: 可选筛选条件
    :return: DataFrame
    """
    logger.info(f"Fetching top {top_n} concept boards")
    df = get_concept_board_top10()

    if filter_by:
        # 示例：filter_by = {'涨幅': 5}
        for col, value in filter_by.items():
            df = df[df[col] > value]

    return df.head(top_n)
