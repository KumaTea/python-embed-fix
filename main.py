import os
import shutil
import zipfile
import requests
import subprocess

EMBED_ZIP_URL = 'https://www.python.org/ftp/python/{ver}/{file}'
GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
GET_PIP_VER_URL = 'https://bootstrap.pypa.io/pip/{ver}/get-pip.py'
GET_PIP_SUPPORTED_AFTER = 8
PIP_INDEX = 'https://pypi.org/simple/pip/'


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


def get_whl_link(pkg: str = 'pip') -> tuple[str, str]:
    pkg_index = f'https://pypi.org/simple/{pkg}/'
    response = requests.get(pkg_index)
    lines = response.text.splitlines()
    pkg_whl_list = []
    for line in lines:
        if pkg in line and 'whl' in line and 'href' in line:
            pkg_whl_list.append(line)
    latest_pkg_whl = pkg_whl_list[-1]
    latest_pkg_whl_link = latest_pkg_whl.split('href="')[1].split('"')[0]
    latest_pkg_whl_name = latest_pkg_whl_link.split('/')[-1].split('#')[0]
    return latest_pkg_whl_name, latest_pkg_whl_link


def get_pkg(pkg: str = 'pip') -> str:
    pkg_whl_name, pkg_whl_link = get_whl_link(pkg)
    pkg_whl_path = os.path.join('tmp', pkg_whl_name)
    if not os.path.isfile(pkg_whl_path):
        with open(pkg_whl_path, 'wb') as f:
            f.write(requests.get(pkg_whl_link).content)
    return pkg_whl_path


def ensure_pip(work_path: str, py_ver: str = '3.12.0'):
    minor_ver = int(py_ver.split('.')[1])
    python_path = os.path.join(work_path, 'python.exe')
    pip_path = get_pip(py_ver)
    if minor_ver <= GET_PIP_SUPPORTED_AFTER:
        pip_whl_path = get_pkg('pip')
        setuptools_whl_path = get_pkg('setuptools')
        wheel_whl_path = get_pkg('wheel')

        # https://github.com/pypa/pip/issues/2351#issuecomment-69994524
        # subprocess.run([python_path, f'{pip_whl_path}/pip', 'install', '--no-index', pip_whl_path])
        with open(pip_path, 'r') as f:
            script = f.read()
        script = script.replace(
            '["install", "--upgrade", "--force-reinstall"]',
            f'["install", "--no-index", "{pip_whl_path}", "{setuptools_whl_path}", "{wheel_whl_path}"]',
            1
        )
        tmp_pip_path = os.path.join('tmp', 'get-pip-tmp.py')
        with open(tmp_pip_path, 'w') as f:
            f.write(script)
        subprocess.run([python_path, tmp_pip_path, '--no-warn-script-location'])
        os.remove(tmp_pip_path)
    else:
        subprocess.run([python_path, pip_path, '--no-warn-script-location'])


def pack_embed(work_path: str, out_path: str):
    with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(work_path):
            for file in files:
                z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), work_path))


def process_assets(work_path: str):
    for file in os.listdir('assets'):
        shutil.copy(os.path.join('assets', file), os.path.join(work_path, file))

    files = os.listdir(work_path)
    python_pth_list = [f for f in files if f.startswith('python3') and f.endswith('._pth')]
    if python_pth_list:
        python_pth = python_pth_list[0]
        os.remove(os.path.join(work_path, python_pth))
        os.rename(os.path.join(work_path, 'python._pth'), os.path.join(work_path, python_pth))
    else:
        os.remove(os.path.join(work_path, 'python._pth'))


def test_python(work_path: str):
    print(f'Testing Python {work_path}...')
    python_path = os.path.join(work_path, 'python.exe')
    return subprocess.run([python_path, '-V'])


def test_pip(work_path: str):
    print(f'Testing pip {work_path}...')
    python_path = os.path.join(work_path, 'python.exe')
    return subprocess.run([python_path, '-m', 'pip', '-V'])


def main(py_ver: str = '3.12.0', platform: str = 'amd64'):
    print(f'Processing Python {py_ver} for {platform}')
    filename = f'python-{py_ver}-embed-fix-{platform}.zip'
    out_path = os.path.join('out', filename)
    if os.path.isfile(out_path):
        return print(f'Embed already exists: {out_path}')

    init()
    embed_path = get_embed(py_ver, platform)
    work_path = os.path.join('tmp', py_ver)

    print(f'Unzipping {embed_path} to {work_path}...')
    unzip_embed(embed_path, work_path)
    create_dirs(work_path)
    process_assets(work_path)
    test_python(work_path)

    print(f'Packing embeds...')
    pack_embed(work_path, out_path)

    print(f'Ensuring pip...')
    try:
        ensure_pip(work_path, py_ver)
        test_pip(work_path)
        filename = f'python-{py_ver}-embed-pip-{platform}.zip'
        out_path = os.path.join('out', filename)
        pack_embed(work_path, out_path)
    except Exception as e:
        print(f'Failed to ensure pip: {e}')

    print(f'Cleaning up...')
    shutil.rmtree(work_path)


if __name__ == '__main__':
    for version in [
        '3.5.4', '3.6.8', '3.7.9',  # end of life
        '3.8.10', '3.9.13', '3.10.11', '3.11.9', '3.12.7', '3.13.0'
    ]:
        main(version)
