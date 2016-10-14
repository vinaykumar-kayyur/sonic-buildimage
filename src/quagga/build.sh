#!/bin/bash -x

cd sonic-quagga
ls -lrt

sudo chmod a+x debian/rules
dpkg-buildpackage -rfakeroot -b -us -uc
cd ..
cp *.deb ..
