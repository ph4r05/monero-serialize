import sys

from setuptools import setup
from setuptools import find_packages

version = '3.0.5'

# Please update tox.ini when modifying dependency version requirements
install_requires = [
    'aiounittest',
]

dev_extras = [
    'nose',
    'pep8',
    'tox',
    'aiounittest',
]

docs_extras = [
    'Sphinx>=1.0',  # autodoc_member_order = 'bysource', autodoc_default_flags
    'sphinx_rtd_theme',
    'sphinxcontrib-programoutput',
]


try:
    import pypandoc, io
    long_description = pypandoc.convert('README.md', 'rst')
    long_description = long_description.replace("\r", '')
    with io.open('README.rst', 'w+', encoding='utf-8') as f:
        f.write(long_description)

except(IOError, ImportError) as e:
    import io
    print("ERROR in readme conversion", e)
    with io.open('README.md', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='monero-serialize',
    version=version,
    description='Monero serialization',
    long_description=long_description,
    url='https://github.com/ph4r05/monero-serialize',
    author='Dusan Klinec',
    author_email='dusan.klinec@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Security',
    ],

    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=install_requires,
    extras_require={
        'dev': dev_extras,
        'docs': docs_extras,
    },
)
