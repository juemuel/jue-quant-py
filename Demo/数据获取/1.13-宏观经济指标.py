from common import *
from qstock import plot

# 获取中国GDP指标
df = ak.macro_china_gdp()
df = df.sort_index(ascending=False)
print(df)
# 保留绝对值的列
df = df.loc[:, ['季度', '国内生产总值-同比增长', '第一产业-同比增长', '第二产业-同比增长', '第三产业-同比增长']]
# DataFrame装成Series,索引是 '季度' 列
series_df = df.set_index('季度')
# qstock 对比折线图
plot.line(series_df, title='中国GDP')
