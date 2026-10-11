FROM python:3.11-slim
WORKDIR /app
COPY common_node.py .
COPY app.py .
ENV NODE_ID=cs-node-api
ENV SERVICE_NAME=api
ENV PORT=8002
EXPOSE 8002
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"
CMD ["python", "app.py"]
