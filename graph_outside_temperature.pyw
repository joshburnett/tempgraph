# -*- coding: utf-8 -*-

from pathlib import Path

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import sys
from graphWindowUI import Ui_GraphWindow

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from datetime import datetime, date, timedelta

from darksky import forecast

from PIL import Image, ImageDraw, ImageFont
import subprocess

pyqtSignal = QtCore.pyqtSignal


DARKSKY_KEY = 'c0b3acd5867eaa852edffa5c8bee6744'


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    forecast_received = pyqtSignal('PyQt_PyObject')

    def __init__(self, icon, graph_window, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)

        self.graph_window = graph_window
        self.setIcon(QtGui.QIcon("blank.png"))

        # Set up context menu
        self.menu = QtWidgets.QMenu(parent)
        change_icon = self.menu.addAction("Update Forecast")
        exit_action = self.menu.addAction("Exit")
        self.setContextMenu(self.menu)
        exit_action.triggered.connect(self.quit)
        change_icon.triggered.connect(self.update)

        self.activated.connect(self.on_activated)
        self.forecast_received.connect(self.graph_window.update_graph)
        self.forecast_received.connect(self.graph_window.update_temperature)

        self.temperature_f = 50
        self.forecast = None

        self.update()

        self.timer = QtCore.QTimer(parent=self)
        self.timer.timeout.connect(self.update)
        # self.timer.start(5000)  # update every 5 seconds
        # self.timer.start(1000*10)  # update every 10 seconds
        # self.timer.start(1000*60)  # update every minute
        self.timer.start(5000*60)  # update every 5 minutes

    def update(self):
        self.graph_window.update_location()
        self.update_temperature()
        self.update_icon()

    def on_activated(self, activation_reason=None):
        if activation_reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.toggle_graph()

    def toggle_graph(self):
        if self.graph_window.isHidden():
            self.show_graph()
        else:
            self.graph_window.hide()

    def show_graph(self):
        desktop_size = QtWidgets.QApplication.desktop().availableGeometry(self.graph_window)
        widget_size = self.graph_window.frameGeometry()

        self.graph_window.move(desktop_size.width()-widget_size.width(), desktop_size.height()-widget_size.height())
        self.graph_window.show()

    def quit(self):
        self.hide()
        QtWidgets.QApplication.quit()

    def update_temperature(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.forecast = forecast(DARKSKY_KEY, *self.graph_window.location)
        except Exception as e:
            print(f'Exception requesting data @ {timestamp}: {e}')
            return

        self.temperature_f = self.forecast.currently.temperature
        self.forecast_received.emit(self.forecast)

    def update_icon(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{timestamp}\tUpdating temperature: {self.temperature_f:.1f}°F')
        final_image_size = 32
        scale_factor = 5
        big_image_size = (final_image_size * scale_factor, final_image_size * scale_factor)
        image = Image.new("RGBA", big_image_size, (10, 10, 10))
        draw = ImageDraw.Draw(image)
        fontsize = int(final_image_size * scale_factor / 1.3)
        font = ImageFont.truetype(r'C:\Windows\Fonts\calibrib.ttf', fontsize)
        txt = '%.0f' % self.temperature_f
        draw.text((18, final_image_size * scale_factor / 5.5), txt, (255, 255, 255), font=font)
        img_resized = image.resize((final_image_size, final_image_size), Image.ANTIALIAS)

        img_resized.save('temperature.png')

        self.setIcon(QtGui.QIcon('temperature.png'))
        self.setToolTip('%.1f°F: ' % self.temperature_f + timestamp)


class GraphWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        # Set up main window
        self.ui = Ui_GraphWindow()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        esc_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), self)
        esc_shortcut.activated.connect(self.hide)

        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()
        self.ui.graph_placeholder.setLayout(QtWidgets.QVBoxLayout())
        self.ui.graph_placeholder.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.graph_placeholder.layout().setSpacing(0)
        self.ui.graph_placeholder.layout().addWidget(self.canvas)

        self.temp_graph = self.fig.add_subplot(111)
        self.precip_graph = self.temp_graph.twinx()

        self.forecast = None
        self.forecast_past = None
        self.history_timestamps = []
        self.history_temps = []
        self.location = (42.4775, -71.2966)  # Bedford, MA
        # self.location = None
        self.update_location()
        self.init_forecast_history()

        self.menu = None

        self.temperature = self.ui.temperature

    def update_location(self):
        # return
        old_location = self.location

        if "Fellowship of the Ping" in subprocess.check_output("netsh wlan show interfaces",
                                                               creationflags=subprocess.CREATE_NO_WINDOW).decode('UTF-8'):
            self.location = (42.6374, -71.4943)  # Groton Rd, Tyngsboro, MA
        else:
            self.location = (42.4775, -71.2966)  # Bedford, MA
        # self.location = (41.907, -71.103)  # Taunton, MA

        if self.location != old_location:
            print('==== Location changed ====')
            self.init_forecast_history()

    def init_forecast_history(self):
        self.forecast = None
        self.forecast_past = None
        self.history_timestamps = []
        self.history_temps = []

        now = datetime.now()
        now_timestamp = now.timestamp()
        today = datetime(now.year, now.month, now.day)
        starttime = int(today.timestamp())

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.forecast_past = forecast(DARKSKY_KEY, *self.location, starttime)
        except Exception as e:
            print(f'Exception requesting data @ {timestamp}: {e}')
            return

        # toss history elements that are in the future
        self.history_timestamps = [point.time for point in self.forecast_past.hourly.data
                                   if point.time < now_timestamp]
        self.history_temps = [point.temperature for point in self.forecast_past.hourly.data
                              if point.time < now_timestamp]

    def update_temperature(self, forecast_data):
        self.temperature.setText(f'{forecast_data.temperature:.0f}°')

    def update_graph(self, forecast_data):
        self.temp_graph.clear()
        self.precip_graph.clear()
        self.forecast = forecast_data
        now = datetime.now()
        now_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        fc_timestamp = self.forecast.currently.time
        print(f'{now_timestamp}\tUpdating weather graph w/ forecast from '
              f'{datetime.fromtimestamp(fc_timestamp).strftime("%H:%M:%S")}')

        history_timestamps = self.history_timestamps
        history_temps = self.history_temps

        # toss history elements that are too old
        xmin = (datetime(now.year, now.month, now.day, now.hour, now.minute)-timedelta(hours=4)).timestamp()

        try:
            while history_timestamps[0] < xmin:
                history_timestamps.pop(0)
                history_temps.pop(0)
        except IndexError:
            # The computer has woken up from being asleep for more than 4 hours,
            # and the while loop above just emptied out the whole history.
            self.init_forecast_history()

        # add current time & temp to history (to connect history with forecast)
        if history_timestamps[-1] != fc_timestamp:
            history_timestamps.append(fc_timestamp)
            history_temps.append(self.forecast.currently.temperature)

        xmax = self.forecast.hourly.data[23].time

        future_timestamps = [fc_timestamp] + \
                            [point.time for point in self.forecast.hourly.data if xmax >= point.time > fc_timestamp]
        future_temps = [self.forecast.currently.temperature] + \
                       [point.temperature for point in self.forecast.hourly.data if xmax >= point.time > fc_timestamp]
        precip_probs = [self.forecast.currently.precipProbability] + \
                       [point.precipProbability for point in self.forecast.hourly.data if xmax >= point.time > fc_timestamp]

        all_temp_data = {timestamp: temperature for timestamp, temperature in
                         zip(history_timestamps + future_timestamps, history_temps + future_temps)}

        # Plot temperature: history first, then forecast
        self.temp_graph.plot(history_timestamps, history_temps, zorder=10, alpha=.3, color='r')
        self.temp_graph.plot(future_timestamps, future_temps, zorder=10, color='r')
        self.temp_graph.plot(self.forecast.currently.time, self.forecast.currently.temperature,'.',
                             markersize=12, color='pink', markeredgecolor='r', zorder=15)

        # Plot freezing
        y_data_min = min(all_temp_data.values())
        y_data_max = max(all_temp_data.values())
        y_data_span = y_data_max-y_data_min
        y_data_avg = y_data_min + y_data_span*0.5

        if y_data_span > 20:
            ymin, ymax = self.temp_graph.get_ylim()
        else:
            if y_data_avg > 40:
                ymax = y_data_max + 12 - (y_data_max % 10)
                ymin = y_data_max - 22
            elif y_data_avg < 20:
                ymin = y_data_min - (y_data_min % 10) - 2
                ymax = ymin + 27
            else:
                ymax = y_data_avg + 12
                ymin = y_data_avg - 12

        self.temp_graph.axhline(y=32, color='b', zorder=5, alpha=0.25)

        # Make list of daily sunrise & sunset times
        sunrise_timestamps = [point.sunriseTime for point in self.forecast.daily.data]
        sunset_timestamps = [point.sunsetTime for point in self.forecast.daily.data]

        # plot day/night regions
        for start, end in zip([xmin] + sunset_timestamps, sunrise_timestamps + [xmax]):
            self.temp_graph.axvspan(start, end, zorder=1, color=(.7, .7, .7), alpha=.3)

        # # plot day delineations
        # day_timestamps = [point.time for point in fc.daily.data]
        # for ts in day_timestamps:
        #     ax1.axvline(ts, color='gray', alpha=.5)

        # set major X ticks to 4 hour increments, minor to 1 hour increments
        start_hour = now.hour - (now.hour % 4)  # start on the last 4-hour increment (unless it's the current hour)
        start_datetime = datetime(now.year, now.month, now.day, start_hour)

        four_hour_inc_datetimes = [start_datetime + timedelta(hours=hours) for hours in range(0, 25, 4)]

        # The graph will show a 24-hour period, and we don't want to put a 4-hour mark at the beginning or the end.
        # So, if we're starting the graph on one of the 4-hour marks, we remove the last timestamp from the list.
        if start_hour == now.hour:
            four_hour_inc_datetimes.pop()

        four_hour_inc_timestamps = [int(dt.timestamp()) for dt in four_hour_inc_datetimes]

        self.temp_graph.set_xticks(four_hour_inc_timestamps)
        self.temp_graph.set_xticklabels([dt.strftime("%I%p").lstrip('0').lower()[:-1] for dt in four_hour_inc_datetimes])

        # we don't want to put a dot or data label on the 4-hour data point that's earlier than now, so we start
        # at index=1
        for ts in four_hour_inc_timestamps[1:]:
            if ts - fc_timestamp > 4000:
                y_offset = (ymax-ymin)*0.05
            else:
                y_offset = (ymax-ymin)*0.075

            if all_temp_data[ts] + y_offset*0.8 > ymax:
                text_yloc = all_temp_data[ts] - y_offset*1.7
            else:
                text_yloc = all_temp_data[ts] + y_offset
            self.temp_graph.text(ts, text_yloc, f'{all_temp_data[ts]:.0f}', ha='center', zorder=20, size='x-small',
                                 va='center')
            self.temp_graph.plot(ts, all_temp_data[ts], '.', color='r', zorder=10)

        major_locator = MultipleLocator(10)
        minor_x_locator = AutoMinorLocator(4)
        self.temp_graph.xaxis.set_minor_locator(minor_x_locator)

        # set major Y ticks to 10 degree increments, minor Y ticks to 5 degrees
        self.temp_graph.yaxis.set_major_locator(major_locator)
        minor_y_locator = AutoMinorLocator(2)
        self.temp_graph.yaxis.set_minor_locator(minor_y_locator)
        self.temp_graph.grid(axis='y', which='major', color=(.5, .5, .5))
        self.temp_graph.grid(axis='y', which='minor', dashes=[5, 5], color=(.8, .8, .8))

        self.temp_graph.tick_params(axis='both', which='both', direction='in', labelsize='x-small')
        # self.temp_graph.tick_params(axis='both', which='major', labelsize=12)

        # self.temp_graph.set_position([-0.1, -0.1, 1, 1])  # set a new position
        self.temp_graph.set_position([0.1, 0.14, 0.88, 0.84])

        # plot precipitation % chance on second Y axis
        self.precip_graph.plot(future_timestamps, precip_probs, color='#0080C0', alpha=.7, zorder=3)
        self.precip_graph.set_ylim(0, 1)
        self.precip_graph.set_yticks([])
        self.precip_graph.fill_between(future_timestamps, precip_probs, color='#0080C0', alpha=.3, zorder=2)

        self.temp_graph.set_xbound(lower=xmin, upper=xmax)
        self.temp_graph.set_ybound(ymin, ymax)
        self.canvas.draw()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()

    graph_window = GraphWindow(w)

    tray_icon = SystemTrayIcon(QtGui.QIcon("blank.png"), graph_window=graph_window)

    tray_icon.show()
    tray_icon.show_graph()
    tray_icon.show_graph()
    # timer = QtCore.QTimer()
    # timer.singleShot(5000, graph_window.hide)

    sys.exit(app.exec_())


if __name__ == '__main__':
    if Path(sys.executable).stem == 'pythonw':
        logdir = Path(__file__).parent / 'logs'
        logdir.mkdir(parents=True, exist_ok=True)
        sys.stdout = open(logdir / datetime.now().strftime('temp grapher %Y-%m-%d %I.%M.%S.log'), 'w')
        sys.stderr = sys.stdout

    main()
