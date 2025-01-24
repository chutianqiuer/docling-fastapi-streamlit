import requests

# Replace with your server's URL
url = "http://127.0.0.1:8020/process/"
file_path = "Finit.pdf"

with open(file_path, "rb") as file:
    response = requests.post(url, files={"file": file})

print(response.json())


import requests

# Replace with your server's URL
url = "http://127.0.0.1:8020/download/processed-file-name"
response = requests.get(url)

if response.status_code == 200:
    with open("downloaded-file-name", "wb") as f:
        f.write(response.content)
    print("File downloaded successfully.")
else:
    print("Failed to download file:", response.status_code)
