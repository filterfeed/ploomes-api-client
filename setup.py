from setuptools import setup, find_packages

setup(
    name="ploomes-api-client",
    version="0.2.147",
    packages=find_packages(),
    url="https://github.com/victorfigueredo/ploomes-api-client",
    author="Victor Figueredo",
    author_email="cto@filterfeed.com.br",
    description="Python client for the Ploomes API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    install_requires=[
        "requests",
        "ratelimit",
        "pandas",
    ],
    python_requires=">=3.6",
)
