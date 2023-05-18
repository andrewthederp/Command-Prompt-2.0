from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
desc = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="command_prompt",
    version="1.2.6",
    description="A copy of command prompt that allows you to easily make cli apps",
    long_description=desc,
    long_description_content_type="text/markdown",
    author="andrew",
    url="https://github.com/andrewthederp/Command_Prompt",
    license="Apache",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    include_package_data=True,
    package_data={
        '': [
            'fonts/*'
        ]
    },
    python_requires=">=3.7",
    packages=find_packages(include=["command_prompt", "command_prompt.*"]),
)

