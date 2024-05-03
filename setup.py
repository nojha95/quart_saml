import setuptools
import os
import re
import sys

here = os.path.abspath(os.path.dirname(__file__))

with open('README.md') as f:
    long_description = f.read()

with open(os.path.join(here, 'quart_saml.py'), 'r') as v_file:
    content = v_file.read()
    pattern = re.compile(r"__version__ = '([^']+)'", re.S)
    print(content)
    match = pattern.search(content)
    if match:
        VERSION = match.group(1)
    else:
        raise ValueError("Version string not found in quart_saml.py")

install_requires = [
    'quart>=0.12.0',
    'blinker>=1.1',
    'pysaml2>=6.5.0',
    'httpx>=0.17.0',
]

setuptools.setup(
    name='Quart-SAML',
    version=VERSION,
    author='Nikhil Ojha',
    install_requires=install_requires,
    url="https://github.com/nojha95/quart_saml",
    author_email='nikhilojha1895@gmail.com',
    description='Quart SAML integration',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['quart_saml'],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.8',
)
