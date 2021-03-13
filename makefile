VERSION := $(shell cat sltxpkg/data/version.info)
SOURCES := sltx $(wildcard sltxpkg/*.py) $(wildcard sltxpkg/data/recipes/*.recipe) requirements.txt setup.py MANIFEST.in README.md sltx-config.yml sltxpkg/data/ LICENSE

.PHONY: all install_local build test version publish


all: test build version

test:
	python3 -m unittest discover -v -s sltxtest

install_local: test build version
	pip3 install --upgrade "dist/sltx-${VERSION}-py3-none-any.whl"
	@echo Please make sure to go back to the normal sltx whenever possible


build: $(SOURCES)
	python3 setup.py sdist bdist_wheel

version:
	@echo "Build with version: ${VERSION}"

publish: test build version
	@if [ $(VERSION) = $(shell cat sltxpkg/data/version.info) ]; then\
		echo "ERROR: You must change the 'VERSION' (${VERSION}) to publish";\
		exit 1; fi
	echo ${VERSION} > sltxpkg/data/version.info
	pipreqs --print > requirements.txt
	git add .
	git commit -s
	git tag -a v${VERSION} -m 'Tag for version v${VERSION}'
	git push --follow-tags
