import os
import requests


EMBED_ZIP_URL = 'https://www.python.org/ftp/python/{ver}/{file}'
GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
GET_PIP_VER_URL = 'https://bootstrap.pypa.io/pip/{ver}/get-pip.py'


def init():
    os.makedirs('tmp', exist_ok=True)
    os.makedirs('out', exist_ok=True)


def get_embed(ver: str = '3.12.0', platform: str = 'amd64'):
    file = f'python-{ver}-embed-{platform}.zip'
    if os.path.exists(os.path.join('tmp', file)):
        return file
    url = EMBED_ZIP_URL.format(ver=ver, file=file)
    with open(file, 'wb') as f:
        f.write(requests.get(url).content)
    return file


def get_pip(py_ver: str = '3.12.0'):
    minor_ver = int(py_ver.split('.')[1])
    if minor_ver >= 8:
        url = GET_PIP_URL
        file = 'get-pip.py'
    else:
        major_ver = int(py_ver.split('.')[0])
        url = GET_PIP_VER_URL.format(ver=f'{major_ver}.{minor_ver}')
        file = f'get-pip-{major_ver}.{minor_ver}.py'

    if os.path.exists(os.path.join('tmp', file)):
        head = requests.head(url)
        size = int(head.headers.get('content-length', -1))
        if size == os.path.getsize(os.path.join('tmp', file)):
            return file

    with open(os.path.join('tmp', file), 'wb') as f:
        f.write(requests.get(url).content)
