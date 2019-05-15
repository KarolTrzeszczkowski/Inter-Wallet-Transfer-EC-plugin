# Inter-Wallet Transfer plugin

The purpose of this plugin i to transfer funds from one wallet to another without compromising anonimity achieved with tools like CashShuffle.

The plugin sends your coins to unused addresses from another wallet at a random time over a selected time period. The coins are sent in one-in-one-out transactions.

After the process is done, the wallet should be emptied of the coins that were there at the beginning of the transfer.
## Installation 
download the latest [release](https://github.com/KarolTrzeszczkowski/Inter-Wallet-Transfer-EC-plugin/releases) zip file, [verify](https://github.com/Electron-Cash/keys-n-hashes#2-verify-sha256-digest-hash) it against [my public key](https://github.com/KarolTrzeszczkowski/Electron-Cash-Last-Will-Plugin/blob/master/pubkey.asc), open your wallet in electron cash, Tools > Installed Plugins and click "Add Plugin". Find the zip file and install it. You should see a new tab in EC interface.

## Usage

At the top of Inter-Wallet Transfer tab you'll see the Master Public Key of the wallet you are looking at. To start transfer between the wallets paste Master Public Key of the wallet you want to transfer your funds to, select the time period for this transfer and hit "Transfer" button. A list of coins in this wallet will be displayed with a predicted, random time of transaction. 

## Donations
If you wish to support development of this plugin or my work in general, consider a donation to the following address:

Cash Account: Licho#14431

bitcoincash:qq93dq0j3uez8m995lrkx4a6n48j2fckfuwdaqeej2

Legacy format: 121dPy31QTsxAYUyGRbwEmW2c1hyZy1Xnz

![donate](donate.png)

