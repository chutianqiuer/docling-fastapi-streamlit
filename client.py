import requests
import argparse

# 创建参数解析器
parser = argparse.ArgumentParser(description="文档处理客户端")
parser.add_argument(
    "--address",
    type=str,
    default="http://127.0.0.1:8020",
    help="服务器地址，默认为 http://127.0.0.1:8020",
)
parser.add_argument(
    "--file_path",
    type=str,
    default="uv.pdf",
    help="要上传的文件路径，默认为 uv.pdf",
)
args = parser.parse_args()

# 使用命令行参数
address = args.address
file_path = args.file_path

# -------------------- 文件上传 --------------------
upload_url = f"{address}/process/"  # 拼接上传URL

try:
    with open(file_path, "rb") as file:
        response = requests.post(upload_url, files={"file": file})

    response.raise_for_status()  # 检查HTTP错误

    print("上传结果:", response.json())

    # 从响应中提取文件名
    try:
        output_directory = response.json()['output_directory']
        file_list = response.json()['files']
        # 获取第一个文件名，这里假设您要下载第一个文件
        processed_file_name = file_list[0]
        print(f"从上传结果中获取的文件名: {processed_file_name}")
    except (KeyError, IndexError) as e:
        print(f"解析上传结果出错: {e}")
        processed_file_name = None  # 或者设置一个默认值，如果无法解析

except requests.exceptions.RequestException as e:
    print(f"上传文件出错: {e}")
    processed_file_name = None  # 确保出错时 processed_file_name 为 None

# -------------------- 文件下载 --------------------
if processed_file_name:  # 只有成功上传并获取文件名后才尝试下载
    download_url = f"{address}/download/{processed_file_name}"  # 拼接下载URL
    downloaded_file_name = f"downloaded-{processed_file_name}"  # 下载后的文件名

    try:
        response = requests.get(download_url, stream=True)  # 使用 stream=True
        response.raise_for_status()  # 检查HTTP错误

        with open(downloaded_file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):  # 分块写入
                f.write(chunk)

        print(f"文件成功下载到: {downloaded_file_name}")

    except requests.exceptions.RequestException as e:
        print(f"下载文件出错: {e}")
else:
    print("由于上传失败，跳过下载步骤。")
