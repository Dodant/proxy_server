import os
import config

os.system(f"cd {config.server_address} && \
    source {config.local_conda_path} && \
    conda activate {config.local_env} && \
    python {config.script}")