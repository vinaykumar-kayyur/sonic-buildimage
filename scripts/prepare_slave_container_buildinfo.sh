#!/bin/bash
  
SLAVE_DIR=$1
ARCH=$2
DISTRO=$3

# Filter the packages installed in the slave container
function filter_packages()
{
    local file=$1
    local build_path=$SLAVE_DIR/../files/build/versions/build
    [ ! -d $build_path ] && return 0
    while read line; do
        if grep -q "$line" $build_path -r; then
            echo $line
        fi
    done < $file
}

# Install the latest debian package sonic-build-hooks in the slave container
sudo dpkg -i --force-overwrite $SLAVE_DIR/buildinfo/sonic-build-hooks_*.deb > /dev/null

# Enable the build hooks
sudo symlink_build_hooks

# Build the slave running config
sudo cp -rf $SLAVE_DIR/buildinfo/* /usr/local/share/buildinfo/
. /usr/local/share/buildinfo/scripts/buildinfo_base.sh

# Enable reproducible mirrors
set_reproducible_mirrors
apt-get update > /dev/null 2>&1

# Build the slave version config
[ -d /usr/local/share/buildinfo/versions ] && rm -rf /usr/local/share/buildinfo/versions
scripts/versions_manager.py generate -t "/usr/local/share/buildinfo/versions" -n "build-${SLAVE_DIR}" -d "$DISTRO" -a "$ARCH"
touch ${BUILDINFO_PATH}/versions/versions-deb

sudo rm -f /etc/apt/preferences.d/01-versions-deb
([ "$ENABLE_VERSION_CONTROL_DEB" == "y" ] && [ -f $VERSION_DEB_PREFERENCE ]) && sudo cp -f $VERSION_DEB_PREFERENCE /etc/apt/preferences.d/

# Install the python packages if existing, skipping none existing packages
([ "$ENABLE_VERSION_CONTROL_PY2" == "y" ] && [ -f $BUILDINFO_PATH/versions/versions-py2 ]) && filter_packages $BUILDINFO_PATH/versions/versions-py2 | xargs -n 1 pip2 install >>$LOG_PATH/error.log 2>&1
([ "$ENABLE_VERSION_CONTROL_PY3" == "y" ] && [ -f $BUILDINFO_PATH/versions/versions-py3 ]) && filter_packages $BUILDINFO_PATH/versions/versions-py3 | xargs -n 1 pip3 install >>$LOG_PATH/error.log 2>&1
exit 0
