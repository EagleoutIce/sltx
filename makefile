VERSION := $(shell cat version.info)
SOURCES := sltx $(wildcard sltxpkg/*.py) requirements.txt setup.py MANIFEST.in README.md sltx-config.yml version.info LICENSE


all: build version

build: $(SOURCES)
	python3 setup.py sdist bdist_wheel

version:
	@echo "Build with version: ${VERSION}"

publish: version
	@if [ $(VERSION) = $(shell cat version.info) ]; then\
		echo "ERROR: You must change the 'VERSION' (${VERSION}) to publish";\
		exit 1; fi
	echo ${VERSION} > version.info
	pip3 freeze > requirements.txt
	git add .
	git commit -s
	git tag -a v${VERSION} -m 'Tag for version v${VERSION}'
	git push --follow-tags