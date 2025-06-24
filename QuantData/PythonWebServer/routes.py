# routes.py
from flask import Blueprint, make_response, request, render_template, current_app
import os
from 数据获取.1_1_K线数据 import get_stock_history_data
# 使用蓝图（组织视图函数、模板和静态文件等）
bp = Blueprint('main', __name__)


# 根路由
@bp.route('/')
def home():
    return 'Welcome to the Home Page!'
# 配置信息路由
@bp.route('/config')
def config_info():
    config_details = current_app.config['ENV']
    return f'Current Configuration: {config_details}'
# 静态路由
@bp.route('/about')
def about():
    return 'This is the About Page.'
# 动态路由
@bp.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}!'
# 处理响应头（make_response）
@bp.route('/response')
def response():
    # 创建响应对象（其中内容为响应内容）
    response = make_response('This is a response page!')
    # 自定义相应标头
    response.headers['X-Custom-Header'] = 'Value'
    return response
# 处理 POST 请求
@bp.route('/submit', methods=['POST'])
def submit():
    # 取出post请求表单数据中的username字段
    username = request.form.get('username')
    return f'Hello, {username}!'

# 嵌入html页面，需要放到temmplates 文件夹下
@bp.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)

@bp.route('/api/v1/index/data')
def get_index_data():
    source = request.args.get('source', 'tushare')
    market = request.args.get('market', 'SH')
    code = request.args.get('code', '000001')

    df = get_stock_history_data(source=source, market=code + '.' + market)
    result = df[['日期', '收盘']].to_dict(orient='records')
    return jsonify(result)