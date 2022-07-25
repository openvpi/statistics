# -*- coding=utf-8
import os

from qcloud_cos import CosConfig, CosServiceError
from qcloud_cos import CosS3Client
from qcloud_cos.cos_threadpool import SimpleThreadPool


secret_id = os.environ.get('secrets.COS_SECRET_ID')
secret_key = os.environ.get('secrets.COS_SECRET_KEY')
if secret_id is None or secret_key is None:
    with open('secret', 'r') as f:
        secret_id = f.readline().strip()
        secret_key = f.readline().strip()

region = 'ap-beijing'
token = None
scheme = 'https'

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)  # 获取配置对象
client = CosS3Client(config)

# 用户的 bucket 信息
test_bucket = 'openvpi-log-1307911855'
start_prefix = 'logs/'
# 对象存储依赖 分隔符 '/' 来模拟目录语义，
# 使用默认的空分隔符可以列出目录下面的所有子节点，实现类似本地目录递归的效果,
# 如果 delimiter 设置为 "/"，则需要在程序里递归处理子目录
delimiter = ''


# 列出当前目录子节点，返回所有子节点信息
def listCurrentDir(prefix):
    file_infos = []
    sub_dirs = []
    marker = ""
    while True:
        response = client.list_objects(test_bucket, prefix, delimiter, marker)

        if "CommonPrefixes" in response:
            common_prefixes = response.get("CommonPrefixes")
            sub_dirs.extend(common_prefixes)

        if "Contents" in response:
            contents = response.get("Contents")
            file_infos.extend(contents)

        if "NextMarker" in response.keys():
            marker = response["NextMarker"]
        else:
            break
    return file_infos


# 下载文件到本地目录，如果本地目录已经有同名文件则会被覆盖；
# 如果目录结构不存在，则会创建和对象存储一样的目录结构
def downloadFiles(file_infos):
    localDir = "./logs/"

    pool = SimpleThreadPool()
    for file in file_infos:
        # 文件下载 获取文件到本地
        file_cos_key = file["Key"]
        localName = localDir + file_cos_key

        # 如果本地目录结构不存在，递归创建
        if not os.path.exists(os.path.dirname(localName)):
            os.makedirs(os.path.dirname(localName))

        # skip dir, no need to download it
        if str(localName).endswith("/"):
            continue

        # 实际下载文件
        # 使用线程池方式
        pool.add_task(client.download_file, test_bucket, file_cos_key, localName)

    pool.wait_completion()
    return None


# 功能封装，下载对象存储上面的一个目录到本地磁盘
def downloadDirFromCos(prefix):
    global file_infos

    try:
        file_infos = listCurrentDir(prefix)
        downloadFiles(file_infos)

    except CosServiceError as e:
        print(e.get_origin_msg())
        print(e.get_digest_msg())
        print(e.get_status_code())
        print(e.get_error_code())
        print(e.get_error_msg())
        print(e.get_resource_location())
        print(e.get_trace_id())
        print(e.get_request_id())
        raise e


if __name__ == "__main__":
    downloadDirFromCos(start_prefix)
