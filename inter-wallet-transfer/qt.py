from PyQt5 import QtGui
from PyQt5 import QtCore

from electroncash.i18n import _
from electroncash.plugins import BasePlugin, hook
from electroncash_gui.qt.util import destroyed_print_error
from electroncash.util import finalization_print_error

from . import ui


class Plugin(BasePlugin):
    electrumcash_qt_gui = None
    # There's no real user-friendly way to enforce this.  So for now, we just calculate it, and ignore it.
    is_version_compatible = True

    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)

        self.wallet_windows = {}
        self.lw_tabs = {}
        self.lw_tab = {}

    def fullname(self):
        return 'Inter-Wallet Transfer'

    def diagnostic_name(self):
        return "InterWalletTransfer"

    def description(self):
        return _("Plugin Inter-Wallet Transfer")

    def on_close(self):
        """
        BasePlugin callback called when the wallet is disabled among other things.
        """
        for window in list(self.wallet_windows.values()):
            self.close_wallet(window.wallet)

    @hook
    def update_contact(self, address, new_entry, old_entry):
        self.print_error("update_contact", address, new_entry, old_entry)

    @hook
    def delete_contacts(self, contact_entries):
        self.print_error("delete_contacts", contact_entries)

    @hook
    def init_qt(self, qt_gui):
        """
        Hook called when a plugin is loaded (or enabled).
        """
        self.electrumcash_qt_gui = qt_gui
        # We get this multiple times.  Only handle it once, if unhandled.
        if len(self.wallet_windows):
            return

        # These are per-wallet windows.
        for window in self.electrumcash_qt_gui.windows:
            self.load_wallet(window.wallet, window)

    @hook
    def load_wallet(self, wallet, window):
        """
        Hook called when a wallet is loaded and a window opened for it.
        """
        wallet_name = window.wallet.basename()
        self.wallet_windows[wallet_name] = window
        self.print_error("wallet loaded")
        self.add_ui_for_wallet(wallet_name, window)
        self.refresh_ui_for_wallet(wallet_name)

    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        window = self.wallet_windows[wallet_name]
        del self.wallet_windows[wallet_name]
        self.remove_ui_for_wallet(wallet_name, window)

    @staticmethod
    def _get_icon() -> QtGui.QIcon:
        if QtCore.QFile.exists(":icons/preferences.png"):
            icon = QtGui.QIcon(":icons/preferences.png")
        else:
            # png not found, must be new EC; try new EC icon -- svg
            icon = QtGui.QIcon(":icons/preferences.svg")
        return icon

    def add_ui_for_wallet(self, wallet_name, window):
        l = ui.LoadRWallet(window, self, wallet_name)
        tab = window.create_list_tab(l)
        self.lw_tabs[wallet_name] = tab
        self.lw_tab[wallet_name] = l

        window.tabs.addTab(tab, self._get_icon(), _('Inter-Wallet Transfer'))

    def remove_ui_for_wallet(self, wallet_name, window):

        wallet_tab = self.lw_tabs.get(wallet_name)
        widget = self.lw_tab.get(wallet_name)
        if wallet_tab is not None:
            if widget and callable(getattr(widget, 'kill_join', None)):
                widget.kill_join()  # kill thread, wait for up to 2.5 seconds for it to exit
            if widget and callable(getattr(widget, 'clean_up', None)):
                widget.clean_up()  # clean up wallet and stop its threads
            del self.lw_tab[wallet_name]
            del self.lw_tabs[wallet_name]
            if wallet_tab:
                i = window.tabs.indexOf(wallet_tab)
                window.tabs.removeTab(i)
                wallet_tab.deleteLater()
                self.print_error("Removed UI for", wallet_name)

    def refresh_ui_for_wallet(self, wallet_name):
        wallet_tab = self.lw_tabs.get(wallet_name)
        if wallet_tab:
            wallet_tab.update()
        wallet_tab = self.lw_tab.get(wallet_name)
        if wallet_tab:
            wallet_tab.update()

    def switch_to(self, mode, wallet_name, recipient_wallet, time, password):
        window=self.wallet_windows[wallet_name]
        try:
            l = mode(window, self, wallet_name, recipient_wallet,time, password=password)

            tab = window.create_list_tab(l)
            destroyed_print_error(tab)  # track object lifecycle
            finalization_print_error(tab)  # track object lifecycle

            old_tab = self.lw_tabs.get(wallet_name)
            i = window.tabs.indexOf(old_tab)

            self.lw_tabs[wallet_name] = tab
            self.lw_tab[wallet_name] = l
            window.tabs.addTab(tab, self._get_icon(), _('Inter-Wallet Transfer'))
            if old_tab:
                window.tabs.removeTab(i)
                old_tab.searchable_list.deleteLater()
                old_tab.deleteLater()  # Qt (and Python) will proceed to delete this widget
        except Exception as e:
            self.print_error(repr(e))
            return
