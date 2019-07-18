#!/bin/bash

plugname=inter-wallet-transfer
dirname=inter-wallet-transfer

echome=$HOME/.electron-cash
dest=$echome/external_plugins/${plugname}.zip

if [ ! -d "$echome" ]; then
    echo "Cannot find $echome"
    exit 1
fi

force=""
if [ "$1" == "-f" -o "$1" == "--force" ]; then
	force="1"
fi

if [ -e "$dest" -a -z "$force" ]; then
    echo "$dest already exists, overwrite? [y/N] "
    read reply
    if [ "$reply" != "y" ]; then
        echo "Ok, giving up..."
        exit 1
    fi
fi

dn=`dirname -- $0`


pushd "$dn" > /dev/null 2>&1

rm -f ${plugname}.zip
zip -rp -9 ${plugname}.zip ${dirname} manifest.json
mv -vf ${plugname}.zip "$dest"
echo "Done."
popd > /dev/null 2>&1
exit 0

