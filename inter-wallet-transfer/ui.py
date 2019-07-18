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
from electroncash.util import PrintError, print_error
import time, datetime, random, threading, tempfile, string, os, queue
import weakref


class LoadRWallet(MessageBoxMixin, PrintError, QDialog):

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
        l = QLabel(_("How long the transfer should take (in whole hours): "))
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
        # comment the below out if you want to disable auto-clean of temp file
        # otherwise the temp file will be auto-cleaned on app exit or
        # on this object's destruction
        self._finalizer = weakref.finalize(self, self.delete_temp_wallet_file, self.file)

    @staticmethod
    def delete_temp_wallet_file(file):
        ''' deletes the wallet file '''
        if file and os.path.exists(file):
            try:
                os.remove(file)
                print_error("[InterWalletTransfer] Removed temp file", file)
            except Exception as e:
                print_error("[InterWalletTransfer] Failed to remove temp file", file, "error: ", repr(e))

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
            value = self.main_window.format_amount_and_units(u['value'])
            item = SortableTreeWidgetItem([address, value, time.strftime('%H:%M',self.times[i+1])])
            item.setData(2,Qt.UserRole+1,self.times[i+1])
            item.setTextAlignment(1,Qt.AlignRight)
            self.addChild(item)




class Transfer(MessageBoxMixin, PrintError, QDialog):

    switch_signal = pyqtSignal()

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
        self.switch_signal.connect(self.switch_signal_slot)
        self.sleeper = queue.Queue()
        self.t = threading.Thread(target=self.send_all, daemon=True)
        self.t.start()


    def delta(self, time):
        times = [random.randint(0,time*3600) for t in range(len(self.utxos))]
        times.insert(0,0)
        times.sort()
        distances = [times[i+1]-times[i] for i in range(len(times)-1)]
        return distances, times

    def send_all(self):
        ''' Runs in a thread '''
        def wait(timeout=1.0) -> bool:
            try:
                self.sleeper.get(timeout=timeout)
                # if we get here, we were notified to abort.
                return False
            except queue.Empty:
                '''Normal course of events, we slept for timeout seconds'''
                return True
        for i, t in enumerate(self.distances):
            for s in range(t):
                if not wait():
                    # abort signalled
                    return
            coin = self.utxos.pop(0)
            while not self.recipient_wallet.is_up_to_date():
                ''' We must wait for the recipient wallet to finish synching...
                Ugly hack.. :/ '''
                self.print_error("Receiving wallet is not yet up to date... waiting... ")
                if not wait(5.0):
                    # abort signalled
                    return
            self.send_tx(coin)
        # Emit a signal which will end up calling switch_signal_slot
        # in the main thread; we need to do this because we must now update
        # the GUI, and we cannot update the GUI in non-main-thread
        # See issue #10
        self.switch_signal.emit()

    def switch_signal_slot(self):
        ''' Runs in GUI (main) thread '''
        self.plugin.switch_to(LoadRWallet, self.wallet_name, None, None, None)

    FEE = 192

    def send_tx(self,coin):
        self.wallet.add_input_info(coin)
        inputs = [coin]
        recpient_address = self.recipient_wallet.get_unused_address()
        if coin['value'] - self.FEE < self.recipient_wallet.dust_threshold():
            return
        outputs = [(TYPE_ADDRESS, recpient_address, coin['value'] - self.FEE)]
        tx = Transaction.from_io(inputs, outputs, locktime=0)
        self.wallet.sign_transaction(tx, self.password)
        self.main_window.network.broadcast_transaction2(tx)

    def abort(self):
        self.kill_join()
        self.switch_signal.emit()

    def kill_join(self):
        if self.t.is_alive():
            self.sleeper.put(None)  # notify thread to wake up and exit
            if threading.current_thread() is not self.t:
                self.t.join(timeout=2.5)  # wait around a bit for it to die but give up if this takes too long

    def on_delete(self):
        pass

    def on_update(self):
        pass
