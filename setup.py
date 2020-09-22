import setuptools

with open('README.md', 'r') as readme:
    long_description = readme.read()

with open('version.info', 'r') as fv:
    version = fv.readline()

setuptools.setup(
    name="sltx",
    version=version,
    author="Florian Sihler",
    author_email="florian.sihler@uni-ulm.de",
    description="sltx-utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['PyYAML'],
    scripts=['sltx'],
    url="https://github.com/EagleoutIce/sltx",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
        'Environment :: Console'
    ],
    python_requires='>=3.5',
)