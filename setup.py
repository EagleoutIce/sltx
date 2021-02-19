import setuptools

with open('README.md', 'r') as readme:
	long_description = readme.read()

with open('sltxpkg/data/version.info', 'r') as fv:
	version = fv.readline()

setuptools.setup(
	name="sltx",
	version=version,
	author="Florian Sihler",
	author_email="florian.sihler@uni-ulm.de",
	description="sltx-utility",
	long_description=long_description,
	long_description_content_type="text/markdown",
	install_requires=['PyYAML', 'docker', 'importlib_resources'],
	scripts=['sltx'],
	url="https://github.com/EagleoutIce/sltx",
	packages=setuptools.find_packages(),
	package_data={
		'data': ['sltxpkg/data/version.info', 'sltxpkg/data/sltx-dep.yaml'],
		'data/recipes': ['sltxpkg/data/recipes/default-latexmk.recipe','sltxpkg/data/recipes/compress-latexmk.recipe'],
		'data/latexmk/configs': ['data/latexmk/configs/glossary.mkrc', 'data/latexmk/configs/index.mkrc']
	},
	include_package_data=True,
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		'Intended Audience :: Developers',
		'Environment :: Console'
	],
	python_requires='>=3.5',
)