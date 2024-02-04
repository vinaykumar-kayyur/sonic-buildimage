#
# Copyright (c) 2019-2021 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = component-versions

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	echo "SDK $(MLNX_SDK_VERSION)" >> $(DEST)/$(MAIN_TARGET)
	echo $(MLNX_SPC_FW_VERSION) | sed -r 's/([0-9]*)\.([0-9]*)\.([0-9]*)/FW \2\.\3/g' >> $(DEST)/$(MAIN_TARGET)
	echo "SAI $(MLNX_SAI_VERSION)" >> $(DEST)/$(MAIN_TARGET)
	echo "HW-MGMT $(MLNX_HW_MANAGEMENT_VERSION)" >> $(DEST)/$(MAIN_TARGET)
	echo "MFT $(MFT_VERSION)" >> $(DEST)/$(MAIN_TARGET)
	echo "Kernel $(KVERSION_SHORT)" >> $(DEST)/$(MAIN_TARGET)
	 