FROM python:3.7

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && \
    ln -sf /dev/stdout /app/stock_log.log

EXPOSE 8000

CMD ["python", "check_stock.py"]