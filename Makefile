.PHONY: setup-build create-feedstock rerender-feedstock build upload
branch ?= gen-five-pkg
PWD=$(shell pwd)
version=$(shell git describe --tags | cut -c 1-7 )
conda ?= $(or $(CONDA_EXE),$(shell find /opt/*conda*/bin $(HOME)/*conda*/bin -type f -iname conda))
conda_bin := $(patsubst %/conda,%,$(conda))
conda_act := $(conda_bin)/activate
conda_act_cmd := source $(conda_act)
sed_v = s/VERSION/$(version)/
sed_b = s/BRANCH/$(branch)/g
build_dir = $(shell $(conda) build --output -m .ci_support/linux_64_.yaml recipe/)

setup-build:
	echo "...setup-build..."
	$(conda) create -n build-pub -c conda-forge conda-build conda-smithy anaconda-client

create-feedstock:
	echo "xxx version: $(version)"
	echo "xxx branch: $(branch)"
	mkdir -p $(WORKDIR)/esg-publisher-feedstock;
	$(conda_act_cmd) build-pub && \
	cd $(WORKDIR)/esg-publisher-feedstock && $(conda) smithy ci-skeleton $(WORKDIR)/esg-publisher-feedstock;
	mkdir -p $(WORKDIR)/esg-publisher-feedstock/recipe 
	cp $(PWD)/recipe/meta.yaml $(WORKDIR)/esg-publisher-feedstock/recipe/meta.yaml
	sed -i "$(sed_v)" $(WORKDIR)/esg-publisher-feedstock/recipe/meta.yaml
	sed -i "$(sed_b)" $(WORKDIR)/esg-publisher-feedstock/recipe/meta.yaml

rerender-feedstock:
	cd $(WORKDIR)/esg-publisher-feedstock && \
	$(conda_act_cmd) build-pub && \
	$(conda) smithy rerender;

build: setup-build create-feedstock rerender-feedstock
	cd $(WORKDIR)/esg-publisher-feedstock && \
	$(conda_act_cmd) build-pub && \
	$(conda) build -m .ci_support/linux_64_.yaml recipe/
	echo "$(build_dir)"

upload:
	$(conda_act_cmd) build-pub && \
	anaconda -t $(TOKEN) upload $(build_dir) -u esgf-forge
