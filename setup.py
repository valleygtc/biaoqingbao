from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

meta = {}
exec((here / 'src/biaoqingbao/version.py').read_text(encoding='utf-8'), meta)

setup(
    name='biaoqingbao',
    version=meta['__version__'],
    description='Image manager with web UI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/valleygtc/biaoqingbao',
    author='gutianci',
    author_email='gutianci@qq.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Desktop Environment',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Operating System :: OS Independent",
    ],
    keywords='application web',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6',
    install_requires=['flask', 'flask-sqlalchemy', 'psycopg2', 'waitress', 'PyJWT'],
    extras_require={
        'dev': ['pylint', 'rope'],
        'deploy': ['gunicorn'],
    },
    entry_points={
        'console_scripts': [
            'biaoqingbao=biaoqingbao:cli',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/valleygtc/biaoqingbao/issues',
        'Source': 'https://github.com/valleygtc/biaoqingbao/',
    },
)
