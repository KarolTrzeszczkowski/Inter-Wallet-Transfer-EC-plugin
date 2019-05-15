# Inter-Wallet Transfer plugin
The purpose of this plugin is to transfer funds from one wallet to another without compromising anonymity achieved with tools like CashShuffle.

To do this, it sends your coins to unused addresses from another wallet at random times over a selected time period. The coins are sent in one-in-one-out transactions.

After the process is completed, the wallet should be emptied of the coins that were there at the beginning of the transfer.

## Installation 
Download the latest [release](https://github.com/KarolTrzeszczkowski/Inter-Wallet-Transfer-EC-plugin/releases) (which will be a .zip file), [verify](https://github.com/Electron-Cash/keys-n-hashes#2-verify-sha256-digest-hash) it against [my public key](https://github.com/KarolTrzeszczkowski/Electron-Cash-Last-Will-Plugin/blob/master/pubkey.asc),open your wallet in electron cash, click the “Tools” drop down menu, click “Installed Plugins”, click "Add Plugin", find and open the zip file, confirm the “risks and dangers” boxes, and click install. You should now see a new tab in EC interface.

## Usage
To start a transfer from the wallet you have open, first paste the receiving wallet’s Master Public Key (which starts with xpub for mainnet wallets) in the first dialogue box in the “Inter-Wallet Transfer” plugin tab. Next, enter the amount of time you want the transfer to take. (Within that amount of time, all funds will be transferred to the receiving wallet at randomly selected intervals.) Finally, hit the "Transfer" button. A list of coins in this wallet will be displayed with their predicted time of transaction, and the transfer will begin. The wallet must be kept open during the process.
## Special thanks  
I want to thank Imaginary_Username for funding the bounty for this plugin, and all the people that helped me with beta tests and code review, highlighting: Emergent_reasons, John Moriarty and NilacTheGrim.

## Donations
If you wish to support development of this plugin or my work in general, consider a donation to the following address:

Cash Account: Licho#14431

bitcoincash:qq93dq0j3uez8m995lrkx4a6n48j2fckfuwdaqeej2

Legacy format: 121dPy31QTsxAYUyGRbwEmW2c1hyZy1Xnz

![donate](donate.png)

