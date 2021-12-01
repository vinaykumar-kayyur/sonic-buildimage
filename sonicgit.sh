#!/bin/bash
source ./build.cfg
 
if [ -d "${BLDDIR}" ];then
   echo "directory sonic-buildimage already exists, aborting git"
   exit 1
fi
 
# git clone the top-level
# source code from the public repository, SONICBRANCH=201911
 
git clone -b ${SONICBRANCH} https://github.com/anselmes/sonic-buildimage.git
 
# move the cloned source to a build-specific named directory
# avoid overwriting earlier versions that you may need.
mv ./sonic-buildimage "${BLDDIR}"
 
# If you are making any changes to the latest checked in branch, you must make
# changes to the configuration.
# Because you are making changes, create a build branch based on the specific commit hash
#this git branch information shows up in the build image,
#when you run command $show version from the switch command line.
 
cd "${BLDDIR}"
git checkout -b "${BLDBRANCH}" ${COMMITHASH}
 
# the git clone step only pulls the top-level module.
# the underlying submodules must be recursively
# init-ed and updated.
 
git submodule update --init --recursive
 
#display the status
echo "${BLDDIR}"
git status | grep branch