#!/bin/bash -x

mkdir quagga

wget -O quagga_0.99.24.1.tar.gz https://github.com/Azure/sonic-quagga/archive/debian/0.99.24.1.tar.gz
tar -xzf quagga_0.99.24.1.tar.gz -C quagga --strip 1

ls -lrt

cd quagga
ls -lrt

sudo chmod a+x debian/rules
dpkg-buildpackage -rfakeroot -b -us -uc
cd ..
cp *.deb ..
