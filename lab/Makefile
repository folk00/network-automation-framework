# Lab orchestration — containerlab + cEOS + Ansible.
#
# Targets:
#   make up         spin up the 3-node lab
#   make down       tear it down (keeps the image)
#   make destroy    tear down + remove network state
#   make reach      ansible reachability check
#   make render     ansible: render configs only
#   make dryrun     ansible: connect + show diff vs running
#   make deploy     ansible: push OSPF config + validate neighbors
#   make validate   ansible: only run the post-checks
#   make all        up + reach + deploy + validate
#   make logs       tail clab events for the running lab
#
# Requirements: docker, containerlab, ansible-core, cisco/arista collections.
# Image: ceos:4.32.0F (download from arista.com after free signup, then
#        `docker import cEOS-lab-4.32.0F.tar ceos:4.32.0F`).

LAB_DIR    := $(CURDIR)
ANSIBLE    := ansible-playbook -i ../ansible/inventories/clab.yml
PB_DIR     := ../ansible/playbooks
CEOS_IMAGE ?= ceos:4.32.0F

.PHONY: help up down destroy reach render dryrun deploy validate all logs check-image

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) || \
	  awk '/^[a-zA-Z_-]+:/ {gsub(/:.*/,""); print "  make "$$0}' $(MAKEFILE_LIST)

check-image:
	@docker image inspect $(CEOS_IMAGE) >/dev/null 2>&1 || { \
	  echo "ERROR: image '$(CEOS_IMAGE)' not found locally."; \
	  echo "       Download cEOS-lab from arista.com (free) and run:"; \
	  echo "       docker import cEOS-lab-4.32.0F.tar $(CEOS_IMAGE)"; \
	  exit 1; }

up: check-image
	CEOS_IMAGE=$(CEOS_IMAGE) sudo -E containerlab deploy -t topology.clab.yml

down:
	sudo containerlab destroy -t topology.clab.yml

destroy:
	sudo containerlab destroy -t topology.clab.yml --cleanup

reach:
	$(ANSIBLE) $(PB_DIR)/check_reachability.yml

render:
	$(ANSIBLE) $(PB_DIR)/render.yml --connection=local

dryrun:
	$(ANSIBLE) $(PB_DIR)/dry_run.yml --diff

deploy:
	$(ANSIBLE) $(PB_DIR)/deploy.yml

validate:
	$(ANSIBLE) $(PB_DIR)/deploy.yml --tags validate

all: up reach deploy validate

logs:
	sudo containerlab inspect -t topology.clab.yml
