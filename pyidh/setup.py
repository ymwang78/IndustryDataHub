from setuptools import setup, find_packages

setup(
    name="pyidh",
    version="0.1.1",
    packages=find_packages(),
    package_data={
        "pyidh": ["libidh.dll"],
    },
    install_requires=[
        "pywin32>=305",
    ],
    author="Yongming Wang",
    author_email="wangym@gmail.com",
    description="Python wrapper for Industry Data Hub",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ymwang78/IndustryDataHub",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
) 