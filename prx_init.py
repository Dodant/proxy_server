import os

os.system(f"cd ~/Documents/proxy_server && \
    source /opt/homebrew/anaconda3/etc/profile.d/conda.sh && \
    conda activate prx && \
    python server.py")