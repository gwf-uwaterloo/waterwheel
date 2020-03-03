from setuptools import setup
import os

def readme():
    with open(os.path.dirname(os.path.realpath(__file__)) + '/README.md') as f:
        return f.read()

requires = [
    'spacy',
    'tqdm',
    'pandas'
]
setup(
    name="waterwheel",
    version="0.1",
    author="Govind Sharma",
    author_email="govind.sharma@uwaterloo.ca",
    description="Spacy Module for Hydrologic Entity Extraction",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/gwf-uwaterloo/waterwheel",
    install_requires=requires,
    packages=['waterwheel'],
    package_data={'waterwheel': [
        'waterwheel/resources/vocab.json',
        'waterwheel/resources/wikidata.json',
        'waterwheel/resources/stop_words.txt',
        'waterwheel/resources/doc_bin.pkl'
    ]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)