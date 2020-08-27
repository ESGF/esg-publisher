.PHONY: setup-build create-feedstock rerender-feedstock build upload

branch ?= gen-five-pkg
version=`cd ~/esg-publisher \ git describe --tags | tr -d '\n'`

setup-build:
	conda create -n build-pub -c conda-forge conda-build conda-smithy anaconda

create-feedstock:
	mkdir $(WORKDIR)/esg-publisher-feedstock
	cd $(WORKDIR)/esg-publisher-feedstock
	conda smithy ci-skeleton $(WORKDIR)/esg-publisher-feedstock
	mkdir recipe
	cp ~/esg-publisher/meta.yaml recipe/meta.yaml
	cd ~/esg-publisher
	cd $(WORKDIR)/esg-publisher-feedstock/recipe
	sed 's/@VERSION@/$(version)' meta.yaml
	sed 's/@BRANCH@/$(branch)' meta.yaml

rerender-feedstock:
	conda activate build-pub
	cd $(WORKDIR)/esg-publisher-feedstock
	conda smithy rerender

build: setup-build create-feedstock rerender-feedstock
	conda build -m .ci_support/linux_64_.yaml recipe/

upload:
	anaconda -t $(TOKEN) upload /export/witham3/anaconda2/conda-bld/noarch/esgcet-5.0.0a-py_0.tar.bz2 -u esgf-forge

