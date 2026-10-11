FROM python:3.11-slim
WORKDIR /app
COPY common_node.py .
COPY app.py .
ENV NODE_ID=cs-node-worker
ENV SERVICE_NAME=worker
ENV PORT=8003
EXPOSE 8003
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')"
CMD ["python", "app.py"]
