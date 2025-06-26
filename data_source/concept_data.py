from commonLib import qs, ak, pd
from pyecharts.charts import TreeMap
from pyecharts import options as opts
# 1.下载https://github.com/pyecharts/pyecharts 2.封装输出到指定地址

def get_concept_board_top10():
    """获取概念板块前十排名"""
    return qs.realtime_data("概念板块").head(10)

def build_treemap_data(df):
    """构建树状图所需数据"""
    data = []
    for index, row in df.iterrows():
        # 定义echarts数据格式
        item = {
            "value": row['涨幅'],
            "name": row['名称'],
            "path": row['名称']
        }
        # 获取板块排名前五的个股
        board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=row['名称']).sort_values(by='涨跌幅',
                                                                                              ascending=False).head(5)
        children = []
        for b_index, b_row in board_concept_cons_em_df.iterrows():
            children_item = {
                "value": row['涨幅'],
                "name": row['名称'],
                "path": row['名称'] + "/" + b_row['名称']
            }
            children.append(children_item)
        item["children"] = children
        data.append(item)
    return data

def generate_treemap(data, date_type="概念板块"):
    """生成树状图"""
    TreeMap().add(
        series_name=date_type,
        data=data,
        width='100%',
        levels=[
            opts.TreeMapLevelsOpts(
                treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(border_color="#555", border_width=4, gap_width=4)
            ),
            opts.TreeMapLevelsOpts(
                color_saturation=[0.3, 0.6],
                treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(border_color_saturation=0.7, gap_width=2, border_width=2)
            ),
            opts.TreeMapLevelsOpts(
                color_saturation=[0.3, 0.5],
                treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(border_color_saturation=0.6, gap_width=1)
            ),
            opts.TreeMapLevelsOpts(color_saturation=[0.3, 0.5]),
        ],
    ).set_global_opts(title_opts=opts.TitleOpts(title=date_type + "-个股排行")) \
        .render("/Users/jvjielv/Downloads/treemap_levels.html")
