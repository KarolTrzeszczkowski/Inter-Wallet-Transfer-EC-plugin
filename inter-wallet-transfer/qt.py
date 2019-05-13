from PyQt5 import QtGui

import electroncash.version, os
from electroncash.i18n import _
from electroncash.plugins import BasePlugin, hook


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
        print("update_contact", address, new_entry, old_entry)

    @hook
    def delete_contacts(self, contact_entries):
        print("delete_contacts", contact_entries)

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
        print("wallet loaded")
        self.add_ui_for_wallet(wallet_name, window)
        self.refresh_ui_for_wallet(wallet_name)


    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        window = self.wallet_windows[wallet_name]
        del self.wallet_windows[wallet_name]
        self.remove_ui_for_wallet(wallet_name, window)


    def add_ui_for_wallet(self, wallet_name, window):
        from .ui import LoadRWallet
        l = LoadRWallet(window, self, wallet_name)
        tab = window.create_list_tab(l)
        self.lw_tabs[wallet_name] = tab
        self.lw_tab[wallet_name] = l
        window.tabs.addTab(tab,  QtGui.QIcon(":icons/preferences.png"), _('Inter-Wallet Transfer'))

    def remove_ui_for_wallet(self, wallet_name, window):

        wallet_tab = self.lw_tabs.get(wallet_name, None)
        self.lw_tab[wallet_name].breaker=True
        if wallet_tab is not None:
            del self.lw_tab[wallet_name]
            del self.lw_tabs[wallet_name]
            i = window.tabs.indexOf(wallet_tab)
            window.tabs.removeTab(i)


    def refresh_ui_for_wallet(self, wallet_name):
        wallet_tab = self.lw_tabs[wallet_name]
        wallet_tab.update()
        wallet_tab = self.lw_tab[wallet_name]
        wallet_tab.update()

    def switch_to(self, mode, wallet_name, recipient_wallet, time, password):
        window=self.wallet_windows[wallet_name]
        try:
            l = mode(window, self, wallet_name, recipient_wallet,time, password=password)

            tab = window.create_list_tab(l)
            i = window.tabs.indexOf(self.lw_tabs.get(wallet_name, None))

            self.lw_tabs[wallet_name] = tab
            self.lw_tab[wallet_name] = l
            window.tabs.addTab(tab,  QtGui.QIcon(":icons/preferences.png"), _('Inter-Wallet Transfer'))
            window.tabs.removeTab(i)
        except Exception as es:
            print(es)
            return