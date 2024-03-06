from common import *

# 获取个股的主营构成记录，格力电器为例
zygc_em_df = ak.stock_zygc_em(symbol='SZ000651')
# 任务：找出最新的一次报告
# tips：按某个字段分组groupby，取出第一个非空值，并排序；再筛选取出最新的报告
new_date = zygc_em_df.groupby('报告日期')['报告日期'].first().sort_values(ascending=False)[0]
# print(new_date)
new_df = zygc_em_df[zygc_em_df['报告日期'] == new_date]
print(new_df)

# 同花顺-上市公司主营介绍
zyjs_ths_df = ak.stock_zyjs_ths(symbol='000651')
print(zyjs_ths_df)

# tushare 上市公司基本信息,需要积分120
pro = ts.pro_api(token)
# df = pro.stock_company(ts_code='000651.SZ', fields=[
# 	"chairman",
# 	"reg_capital",
# 	"province",
# 	"city",
# 	"employees",
# 	"main_business",
# 	"introduction",
# 	"business_scope"
# ])
# print(df)

