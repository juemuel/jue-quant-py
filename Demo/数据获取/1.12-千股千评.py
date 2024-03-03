from comm import *


def filter_stock(df: pd.DataFrame):
	# 剔除出包含ST的股票
	st_data = df[df['名称'].str.contains('ST')]
	sts = st_data['代码'].values.tolist()
	for st in sts:
		df = df.drop(index=df.loc[(df['代码'] == st)].index)
	# 剔除出创业板的股票
	cy_data = df[df['代码'].str.contains('^30')]
	cys = cy_data['代码'].values.tolist()
	for cy in cys:
		df = df.drop(index=df.loc[(df['代码'] == cy)].index)
	# 剔除出科创板的股票
	kc_data = df[df['代码'].str.contains('^68')]
	kcs = kc_data['代码'].values.tolist()
	for kc in kcs:
		df = df.drop(index=df.loc[(df['代码'] == kc)].index)
	# 剔除北交所股票
	bj_data = df[df['代码'].str.contains('BJ')]
	bjs = bj_data['代码'].values.tolist()
	for bj in bjs:
		df = df.drop(index=df.loc[(df['代码'] == bj)].index)
	return df


# 千股千评接口
comment_em_df = ak.stock_comment_em()
# print(comment_em_df)
df = filter_stock(comment_em_df)
print(df.sort_values(by='综合得分', ascending=False))

# 千股千评详情-主力控盘-机构参与度
# stock_comment_detail_zlkp_jgcyd_em_df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol="600000")
# print(stock_comment_detail_zlkp_jgcyd_em_df)

# 千股千评-综合评价-历史评分
# stock_comment_detail_zhpj_lspf_em_df = ak.stock_comment_detail_zhpj_lspf_em(symbol="600000")
# print(stock_comment_detail_zhpj_lspf_em_df)

# 千股千评-市场热度-用户关注指数
# stock_comment_detail_scrd_focus_em_df = ak.stock_comment_detail_scrd_focus_em(symbol="600000")
# print(stock_comment_detail_scrd_focus_em_df)

# 千股千评-市场热度-市场参与意愿
# stock_comment_detail_scrd_desire_em_df = ak.stock_comment_detail_scrd_desire_em(symbol="600000")
# print(stock_comment_detail_scrd_desire_em_df)

# 千股千评-市场热度-日度市场参与意愿
# stock_comment_detail_scrd_desire_daily_em_df = ak.stock_comment_detail_scrd_desire_daily_em(symbol="600000")
# print(stock_comment_detail_scrd_desire_daily_em_df)

# 千股千评-市场热度-市场成本
# stock_comment_detail_scrd_cost_em_df = ak.stock_comment_detail_scrd_cost_em(symbol="600000")
# print(stock_comment_detail_scrd_cost_em_df)
