FROM python:3.11-slim
WORKDIR /app
COPY common_node.py .
COPY app.py .
ENV NODE_ID=cs-node-storage
ENV SERVICE_NAME=storage
ENV PORT=8005
EXPOSE 8005
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')"
CMD ["python", "app.py"]
