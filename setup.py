import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="sltx",
    version="0.0.1",
    author="Florian Sihler",
    author_email="florian.sihler@uni-ulm.de",
    description="sltx-utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EagleoutIce/sltx",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)