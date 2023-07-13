#!/bin/bash

# Script created by the tool UsiScript (http://www.usiscript.com/)

#We check if the folder build exist
#If not, we create it
if [ ! -d build ]; then
	echo "The folder build doesn't exist. We create it"
	mkdir build
fi

rm -r build/*

#We check if the folder build/BBBW1 exist
#If not, we create it
if [ ! -d build/BBBW1 ]; then
	mkdir build/BBBW1
fi

#We check if the folder build/BBBW2 exist
#If not, we create it
if [ ! -d build/BBBW2 ]; then
	mkdir build/BBBW2
fi

#We check if the folder build/BBBW1 exist
#If not, we create it
if [ ! -d build/BBBW3 ]; then
	mkdir build/BBBW3
fi

#We check if the folder build/BBBW4 exist
#If not, we create it
if [ ! -d build/BBBW4 ]; then
	mkdir build/BBBW4
fi

cp -r BBBW/static build/BBBW1

cp BBBW/BBBW1* build/BBBW1

cp BBBW/BBBW2* build/BBBW2

cp BBBW/BBBW3* build/BBBW3

cp BBBW/BBBW4* build/BBBW4