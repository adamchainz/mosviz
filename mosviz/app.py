"""
SpecViz front-end GUI access point. This script will start the GUI.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import signal
import sys
import warnings
import os

# THIRD-PARTY
from astropy.utils.exceptions import AstropyUserWarning

# LOCAL
from .third_party.qtpy.QtWidgets import *
from .third_party.qtpy.QtGui import *
from .third_party.qtpy.QtCore import *
from .ui.widgets.utils import ICON_PATH
from .ui.widgets.windows import MainWindow


class App(object):
    def __init__(self):
        super(App, self).__init__()
        # Instantiate main window object
        self._all_tool_bars = {}

        self.main_window = MainWindow()
        self.menu_docks = QMenu("Plugins")
        self.main_window.menu_bar.addMenu(self.menu_docks)

        self.menu_docks.addSeparator()

        # self.main_window.setDockNestingEnabled(True)

        # Load system and user plugins
        self.load_plugins()

    def load_plugins(self):
        """
        Load pre-built and user-created plugins.
        """
        from .interfaces.registries import plugin_registry

        instance_plugins = plugin_registry.members

        for instance_plugin in sorted(instance_plugins,
                                      key=lambda x: x.priority):
            if instance_plugin.location != 'hidden':
                if instance_plugin.location == 'right':
                    location = Qt.RightDockWidgetArea
                elif instance_plugin.location == 'top':
                    location = Qt.TopDockWidgetArea
                else:
                    location = Qt.LeftDockWidgetArea

                self.main_window.addDockWidget(location, instance_plugin)
                # instance_plugin.show()

                # Add this dock's visibility action to the menu bar
                self.menu_docks.addAction(
                    instance_plugin.toggleViewAction())

        # Resize the widgets now that they are all present
        for ip in instance_plugins:
            ip.setMinimumSize(ip.sizeHint())
            QApplication.processEvents()
            ip.setMinimumHeight(100)

        # Sort actions based on priority
        all_actions = [y for x in instance_plugins for y in x._actions]
        all_categories = {}

        for act in all_actions:
            if all_categories.setdefault(act['category'][0], -1) < \
                    act['priority']:
                all_categories[act['category'][0]] = act['category'][1]

        for k, v in all_categories.items():
            tool_bar = self._get_tool_bar(k, v)

            for act in sorted([x for x in all_actions
                               if x['category'][0] == k],
                              key=lambda x: x['priority'],
                              reverse=True):
                tool_bar.addAction(act['action'])

            tool_bar.addSeparator()

        # Sort tool bars based on priority
        all_tool_bars = self._all_tool_bars.values()

        for tb in sorted(all_tool_bars, key=lambda x: x['priority'],
                         reverse=True):
            self.main_window.addToolBar(tb['widget'])

    def _get_tool_bar(self, name, priority):
        if name is None:
            name = "User Plugins"
            priority = -1

        if name not in self._all_tool_bars:
            tool_bar = QToolBar(name)
            tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tool_bar.setMovable(False)

            tool_bar.setStyleSheet("""
                QToolBar {
                    icon-size: 32px;
                }

                QToolBar QToolButton {
                    height: 48px;
                }
            """)

            self._all_tool_bars[name] = dict(widget=tool_bar,
                                             priority=int(priority),
                                             name=name)
        else:
            if self._all_tool_bars[name]['priority'] == 0:
                self._all_tool_bars[name]['priority'] = priority

        return self._all_tool_bars[name]['widget']


def setup():
    qapp = QApplication(sys.argv)
    # qapp.setGraphicsSystem('native')
    qapp.setWindowIcon(QIcon(os.path.join(ICON_PATH, 'application',
                                          'icon.png')))

    #http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    app = App()
    app.main_window.show()

    return qapp, app


def embed():
    """
    Used when launching the application within a shell, and the application
    namespace is still needed.
    """
    qapp, app = setup()
    qapp.exec_()

    return app


def main():
    """
    Used when launching the application as standalone.
    """
    signal.signal(signal.SIGINT, sigint_handler)
    qapp, app = setup()
    sys.exit(qapp.exec_())


def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    warnings.warn('KeyboardInterrupt caught; specviz will terminate',
                  AstropyUserWarning)
    QApplication.quit()


if __name__ == '__main__':
    main()
