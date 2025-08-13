Remove-Item -Path .venv39 -Recurse -Force
py -0p
python -m venv .venv39 或者用指定版本的python创建虚拟环境
.venv39\Scripts\activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000