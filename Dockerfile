FROM python:3.7

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    ln -sf /dev/stdout /app/stock_log.log

CMD ["python", "main.py"]