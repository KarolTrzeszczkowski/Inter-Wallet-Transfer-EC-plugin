from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from electroncash.i18n import _
from electroncash_gui.qt.util import MessageBoxMixin, MyTreeWidget
from electroncash import keystore
from electroncash.wallet import Standard_Wallet
from electroncash.storage import WalletStorage
from electroncash_gui.qt.util import *
from electroncash.transaction import Transaction,TYPE_ADDRESS
import time, datetime, random, threading, tempfile, string, os


class LoadRWallet(QDialog, MessageBoxMixin):

    def __init__(self, parent, plugin, wallet_name, recipient_wallet=None, time=None, password=None):
        QDialog.__init__(self, parent)
        self.password = password
        self.wallet = parent.wallet
        self.utxos = self.wallet.get_spendable_coins(None, parent.config)
        name = '/tmp_wo_wallet'+''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.file = os.sep.join((tempfile.gettempdir(),name))
        self.tmp_pass = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.storage=None
        self.recipient_wallet=None
        self.keystore=None
        self.plugin = plugin
        self.network = parent.network
        self.wallet_name = wallet_name
        self.keystore = None
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        self.local_xpub = self.wallet.get_master_public_keys()
        l = QLabel(_("Master Public Key") + " of this wallet. It is used to generate all of your addresses.: ")
        l2 = QLabel(self.local_xpub[0])
        vbox.addWidget(l)
        vbox.addWidget(l2)
        l2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        l = QLabel(_("Master Public Key") + " of the wallet you want to transfer your funds to:")
        vbox.addWidget(l)
        self.xpubkey=None
        self.xpubkey_wid = QLineEdit()
        self.xpubkey_wid.textEdited.connect(self.transfer_changed)
        vbox.addWidget(self.xpubkey_wid)
        l = QLabel(_("How long the transfer should take (in hours): "))
        vbox.addWidget(l)
        self.time_e = QLineEdit()
        self.time_e.setMaximumWidth(70)
        self.time_e.textEdited.connect(self.transfer_changed)
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(self.time_e)
        self.speed = QLabel()
        hbox.addWidget(self.speed)
        hbox.addStretch(1)
        self.transfer_button = QPushButton(_("Transfer"))
        self.transfer_button.clicked.connect(self.transfer)
        vbox.addWidget(self.transfer_button)
        self.transfer_button.setDisabled(True)
        vbox.addStretch(1)


    def transfer(self):
        self.show_message("You should not be using either wallets during transfer. Leave Electron-cash active. "
                          "The plugin ceases operation and will have to be re-activated if Electron-cash "
                          "is stopped during the operation.")
        self.storage = WalletStorage(self.file)
        self.storage.set_password(self.tmp_pass, encrypt=True)
        self.storage.put('keystore', self.keystore.dump())
        self.recipient_wallet = Standard_Wallet(self.storage)
        self.recipient_wallet.start_threads(self.network)
        self.plugin.switch_to(Transfer, self.wallet_name, self.recipient_wallet, int(self.time_e.text()), self.password)


    def transfer_changed(self):
        try:
            assert int(self.time_e.text()) > 0
            self.xpubkey = self.xpubkey_wid.text()
            self.keystore = keystore.from_master_key(self.xpubkey)
        except:
            self.speed.setText('')
            self.transfer_button.setDisabled(True)
        else:
            self.transfer_button.setDisabled(False)
            v = len(self.utxos) / int(self.time_e.text())
            self.speed.setText('{0:.2f}'.format(v)+' tx/h on average')


class TransferringUTXO(MyTreeWidget, MessageBoxMixin):

    def __init__(self, parent, tab):
        MyTreeWidget.__init__(self, parent, self.create_menu,[
            _('Address'),
            _('Amount'),
            _('Time')
        ], None, deferred_updates=False)
        print("transferring utxo")
        now = time.time()
        self.times = [ time.localtime(now + s) for s in tab.times ]
        self.utxos = tab.utxos
        self.main_window = parent
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.sortByColumn(2, Qt.AscendingOrder)

    def create_menu(self, position):
        pass

    def update(self):
        if self.wallet and (not self.wallet.thread or not self.wallet.thread.isRunning()):
            return
        super().update()

    def on_update(self):
        self.clear()
        for i, u in enumerate(self.utxos):
            address = u['address'].to_ui_string()
            value = str(u['value'])
            item = SortableTreeWidgetItem([address, value, time.strftime('%H:%M',self.times[i+1])])
            item.setData(2,Qt.UserRole+1,self.times[i+1])
            self.addChild(item)




class Transfer(QDialog, MessageBoxMixin):

    def __init__(self, parent, plugin, wallet_name, recipient_wallet, time, password):
        QDialog.__init__(self, parent)
        self.wallet_name = wallet_name
        self.plugin = plugin
        self.password = password
        self.main_window = parent
        self.wallet = parent.wallet

        if self.wallet.has_password():
            self.main_window.show_error(_(
                "Inter-Wallet Transfer plugin requires the password. "
                "It will be sending transactions from this wallet at a random time without asking for confirmation."))
            self.password = self.main_window.password_dialog()
            if not self.password:
                return

        self.recipient_wallet = recipient_wallet
        self.utxos = self.wallet.get_spendable_coins(None, parent.config)
        random.shuffle(self.utxos)
        self.distances, self.times = self.delta(time)
        self.tu = TransferringUTXO(parent, self)
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        vbox.addWidget(self.tu)
        self.tu.on_update()
        b = QPushButton(_("Abort"))
        b.clicked.connect(self.abort)
        vbox.addWidget(b)
        self.t = threading.Thread(target=self.send_all)
        self.breaker=False
        self.t.start()


    def delta(self, time):
        times = [random.randint(0,time*3600) for t in range(len(self.utxos))]
        times.insert(0,0)
        times.sort()
        distances = [times[i+1]-times[i] for i in range(len(times)-1)]
        return distances, times

    def send_all(self):
        for i, t in enumerate(self.distances):
            for s in range(t):
                time.sleep(1)
                if self.breaker:
                    return
            coin = self.utxos.pop(0)
            self.send_tx(coin)
        self.plugin.switch_to(LoadRWallet, self.wallet_name, None, None, None)


    def send_tx(self,coin):
        self.wallet.add_input_info(coin)
        inputs = [coin]
        recpient_address = self.recipient_wallet.get_unused_address()
        if (coin['value']-192) < 0:
            return
        outputs = [(TYPE_ADDRESS, recpient_address, coin['value']-192)]
        tx = Transaction.from_io(inputs, outputs, locktime=0)
        self.wallet.sign_transaction(tx, self.password)
        self.main_window.network.broadcast_transaction2(tx)

    def abort(self):
        self.breaker = True
        self.plugin.switch_to(LoadRWallet, self.wallet_name, None, None, None)


    def on_delete(self):
        pass

    def on_update(self):
        pass