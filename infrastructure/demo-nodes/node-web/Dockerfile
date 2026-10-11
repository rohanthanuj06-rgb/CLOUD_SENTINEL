FROM python:3.11-slim
WORKDIR /app
COPY common_node.py .
COPY app.py .
ENV NODE_ID=cs-node-web
ENV SERVICE_NAME=web
ENV PORT=8001
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["python", "app.py"]
