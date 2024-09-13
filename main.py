import os
import shutil
import zipfile
import requests
import subprocess


EMBED_ZIP_URL = 'https://www.python.org/ftp/python/{ver}/{file}'
GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
GET_PIP_VER_URL = 'https://bootstrap.pypa.io/pip/{ver}/get-pip.py'


def init():
    os.makedirs('tmp', exist_ok=True)
    os.makedirs('out', exist_ok=True)


def get_embed(ver: str = '3.12.0', platform: str = 'amd64') -> str:
    file = f'python-{ver}-embed-{platform}.zip'
    path = os.path.join('tmp', file)
    if os.path.exists(path):
        return path
    url = EMBED_ZIP_URL.format(ver=ver, file=file)
    with open(path, 'wb') as f:
        f.write(requests.get(url).content)
    return path


def get_pip(py_ver: str = '3.12.0') -> str:
    minor_ver = int(py_ver.split('.')[1])
    if minor_ver >= 8:
        url = GET_PIP_URL
        file = 'get-pip.py'
    else:
        major_ver = int(py_ver.split('.')[0])
        url = GET_PIP_VER_URL.format(ver=f'{major_ver}.{minor_ver}')
        file = f'get-pip-{major_ver}.{minor_ver}.py'

    path = os.path.join('tmp', file)
    if os.path.exists(path):
        head = requests.head(url)
        size = int(head.headers.get('content-length', -1))
        if size == os.path.getsize(path):
            return path

    with open(path, 'wb') as f:
        f.write(requests.get(url).content)
    return path


def create_dirs(work_path: str):
    os.makedirs(os.path.join(work_path, 'DLLs'), exist_ok=True)
    os.makedirs(os.path.join(work_path, 'Lib', 'site-packages'), exist_ok=True)


def unzip_embed(zip_path: str, work_path: str) -> str:
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(work_path)

    out_files = os.listdir(work_path)
    python_zip = [f for f in out_files if f.startswith('python') and f.endswith('.zip')][0]

    lib_path = os.path.join(work_path, 'Lib')
    os.makedirs(lib_path, exist_ok=True)
    with zipfile.ZipFile(os.path.join(work_path, python_zip), 'r') as z:
        z.extractall(lib_path)
    os.remove(os.path.join(work_path, python_zip))

    return work_path


def ensure_pip(work_path: str, py_ver: str = '3.12.0'):
    python_path = os.path.join(work_path, 'python.exe')
    pip_path = get_pip(py_ver)
    subprocess.run([python_path, pip_path, '--no-warn-script-location'])


def pack_embed(work_path: str, out_path: str):
    with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(work_path):
            for file in files:
                z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), work_path))


def process_assets(work_path: str, py_ver: str = '3.12.0'):
    files = os.listdir(work_path)
    python_pth = [f for f in files if f.startswith('python') and f.endswith('._pth')][0]

    os.remove(os.path.join(work_path, python_pth))
    for file in os.listdir('assets'):
        shutil.copy(os.path.join('assets', file), os.path.join(work_path, file))

    os.rename(os.path.join(work_path, 'python._pth'), os.path.join(work_path, python_pth))


def main(py_ver: str = '3.12.0', platform: str = 'amd64'):
    init()
    embed_path = get_embed()
    work_path = os.path.join('tmp', py_ver)

    unzip_embed(embed_path, work_path)
    create_dirs(work_path)
    process_assets(work_path, py_ver)

    filename = f'python-{py_ver}-embed-fix-{platform}.zip'
    out_path = os.path.join('out', filename)
    pack_embed(work_path, out_path)

    ensure_pip(work_path, py_ver)
    filename = f'python-{py_ver}-embed-pip-{platform}.zip'
    out_path = os.path.join('out', filename)
    pack_embed(work_path, out_path)

    shutil.rmtree(work_path)


if __name__ == '__main__':
    main()
