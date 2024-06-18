import os
import config

os.system(f"ssh {config.address} -p {config.port} \
    \"cd {config.path} && \
    source {config.conda_path}/etc/profile.d/conda.sh && \
    conda activate {config.conda_env} && \
    python {config.script}\"")