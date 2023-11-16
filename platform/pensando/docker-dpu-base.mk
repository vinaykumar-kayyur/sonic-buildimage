# docker dpu image for load

DOCKER_DPU_BASE_STEM = docker-dpu-base

DOCKER_DPU_BASE = $(DOCKER_DPU_BASE_STEM).gz

$(DOCKER_DPU_BASE)_URL = https://sonicstorage.blob.core.windows.net/public/docker-dpu-base.gz

DOWNLOADED_DOCKER_IMAGES += $(DOCKER_DPU_BASE)

