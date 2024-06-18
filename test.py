import os

userID, hostIP, port = "compu", "220.117.189.130", 2322
address = f"{userID}@{hostIP}"
file = "test.png"
path = f"/home/{userID}/Downloads/tmp2/image-outpainting_2"

# methods = ['gan', 'sd', 'sr']
methods = ['sd']
for method in methods:
    os.system(f"scp -P {port} ./req_img/input/{file} {address}:{path}/req_img/")
    os.system(f"ssh {address} -p {port} \
        \"curl -X POST -F 'image=@{path}/req_img/{file}' \
        -F 'method={method}' http://127.0.0.1:5001/process_image \
        --output {path}/req_img/{''.join(file.split('.')[:-1])}_{method}.jpg\"")
    os.system(f"scp -P {port} {address}:{path}/req_img/{''.join(file.split('.')[:-1])}_{method}.jpg ./req_img/output/")
    os.system(f"ssh {address} -p {port} \"rm -r {path}/req_img/*\"")