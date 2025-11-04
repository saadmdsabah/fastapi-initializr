from setuptools import setup, find_packages

setup(
    name="fastapi-initializr",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "questionary",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "fastapi-initializr=fastapi_initializr.main:main",
        ],
    },
    python_requires=">=3.8",
)
