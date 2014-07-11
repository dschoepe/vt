from setuptools import setup, find_packages

setup(
    name='vt',
    version='0.1a',
    description='Command-line västtrafik client',
    url='https://github.com/dschoepe/vt',
    author='Daniel Schoepe',
    author_email='daniel@schoepe.org',
    license='GPLv2+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    packages=["vt"],
    install_requires=['requests', "colorama", "tabulate", "pyxdg"],
    package_data={
    },
    data_files=[],
    entry_points={
        'console_scripts': [
            'vt=vt.vt:main',
        ],
    },
)

