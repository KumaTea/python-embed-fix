# python-embed-fix

Since Python 3.5, [an embedded version](https://docs.python.org/3/using/windows.html#the-embeddable-package) in a zip file has been provided along with other distributions.

However, the docs and usages are ambiguous, making this nice portable version hard to use.

Some people have done awesome efforts to improve that. This project goes one step further.

Based on [jtmoon79/PythonEmbed4Win](https://github.com/jtmoon79/PythonEmbed4Win), this project fixes the original versions and packs them, providing an out-of-the-box experience.

## Usage

Download and unzip from [Releases](https://github.com/KumaTea/python-embed-fix/releases).

Run `python.exe`.

The latest version will be [python-latest-embed-fix-amd64.zip](https://github.com/KumaTea/python-embed-fix/releases/latest/download/python-latest-embed-fix-amd64.zip).

Fixed zip with pip installed will be  [python-latest-embed-pip-amd64.zip](https://github.com/KumaTea/python-embed-fix/releases/latest/download/python-latest-embed-pip-amd64.zip).

## Others

* Since Python 3.9, another version packed with pip is also available. Previous versions of Python are currently not provided due to deprecated built-in ssl libraries.
* Python drops Windows XP support since **3.5**, and drops Windows 7 support since **3.9**.
