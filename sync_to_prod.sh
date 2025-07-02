#!/bin/bash

mkdir -p SmritiProdTmp
cp -r app attached_assets README.md SmritiProdTmp/

cd SmritiProd
git pull origin main
rm -rf *
cp -r ../SmritiProdTmp/* .
rm -rf ../SmritiProdTmp

git add .
git commit -m "Safe sync from SmritiV2 at $(date)"
git push origin main
