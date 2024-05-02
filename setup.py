import setuptools
import os
import re
import sys

here = os.path.abspath(os.path.dirname(__file__))

with open('README.md') as f:
    long_description = f.read()

with open(os.path.join(here, 'flask_saml.py')) as v_file:
    VERSION = re.compile(
        r".*__version__ = '(.*?)'",
        re.S).match(v_file.read()).group(1)

install_requires = [
    'quart>=0.12.0',
    'blinker>=1.1',
    'pysaml2>=6.5.0',
    'hhtpx>=0.17.0',
]

setuptools.setup(
    name='Quart-SAML',
    version=VERSION,
    author='Nikhil Ojha',
    install_requires=install_requires,
    author_email='nikhilojha1895@gmail.com',
    description='Quart SAML integration',
    long_description=long_description,
    py_modules=['quart_saml'],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.8',
)
