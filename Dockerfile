FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	UV_COMPILE_BYTECODE=1 \
	UV_LINK_MODE=copy

WORKDIR /app

COPY requirements.txt .
# Uninstall pip/setuptools after installing deps: neither is needed at
# runtime (see entrypoint.sh), and removing them clears the vendored-msgpack
# and setuptools path-traversal CVEs the trivy-image CI job flags.
RUN pip install --no-cache-dir -r requirements.txt && \
	pip uninstall -y pip setuptools

COPY backend_library/ .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# ENTRYPOINT ["/entrypoint.sh"]
# CMD ["tail", "-f", "/dev/null"]
CMD ["bash", "entrypoint.sh"]