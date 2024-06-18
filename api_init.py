import os

userID, hostIP, port = "compu", "220.117.189.130", 2322
address = f"{userID}@{hostIP}"
path = f"/home/{userID}/Downloads/tmp2/image-outpainting_2"
cmd = "/compuworks/anaconda3"

os.system(f"ssh {address} -p {port} \
    \"cd {path} && \
    source {cmd}/etc/profile.d/conda.sh && \
    conda activate msd1_2 && \
    python server.py\"")