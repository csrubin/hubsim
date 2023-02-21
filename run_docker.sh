#!/bin/zsh

# Run container named "streamlit" in interactive+tty mode, remove container when closed,
# port forward from streamlit's default port so it can be accessed

# Add bind mount with -v?
#  docker run -it -v "$(pwd)/source_dir:/app/target_dir" ubuntu bash
docker run --rm -it -p 8501:8501 streamlit
