FROM vllm/vllm-openai:v0.6.3

# Runtime environment variables
ENV HF_HOME=/models

# Install huggingface CLI (for optional runtime download)
RUN pip install --no-cache-dir huggingface_hub

COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose internal port
EXPOSE 8000

ENTRYPOINT [ "/entrypoint.sh" ]


# Start vLLM server
