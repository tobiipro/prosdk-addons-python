# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tobii_research_addons',
    version='0.1.0',
    description='Addons for the Tobii Pro SDK.',
    long_description=long_description,
    url='https://github.com/tobiipro/prosdk-addons-python',
    author='Tobii Pro AB',
    author_email='tobiiprosdk@tobii.com',
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Video :: Capture',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords='tobii research eyetracking sdk tobiipro',
    py_modules=["tobii_research_addons"],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['tobii_research'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    package_data={
        'sample': [],
    },
    project_urls={
        'Bug Reports': 'https://github.com/tobiipro/prosdk-addons-python/issues',
        'Source': 'https://github.com/tobiipro/prosdk-addons-python',
    },
)
