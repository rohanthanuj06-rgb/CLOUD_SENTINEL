FROM python:3.11-slim
WORKDIR /app
COPY common_node.py .
COPY app.py .
ENV NODE_ID=cs-node-auth
ENV SERVICE_NAME=auth
ENV PORT=8004
EXPOSE 8004
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health')"
CMD ["python", "app.py"]
