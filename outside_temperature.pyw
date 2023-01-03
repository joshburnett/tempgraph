# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:03:10 2016
@author: Josh Burnett

Gets the current temperature for Milford, MA every five minutes and displays this in an icon in the system tray.
"""

#%%
from PyQt5 import QtGui, QtWidgets, QtCore
import sys

import requests
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")

        self.setContextMenu(menu)
        exit_action.triggered.connect(QtWidgets.QApplication.quit)

        log_datetime = datetime.now()
        logfname = 'Outside temperature log - ' + log_datetime.strftime('%Y-%m-%d %H%M%S') + '.log'
        self.logfpath = Path.cwd() / 'logs' / logfname

        self.temperature_f = None
        self.update_temperature()

        self.timer = QtCore.QTimer(parent=self)
        self.timer.timeout.connect(self.update_temperature)
        self.timer.start(5000*60)  # update every 5 minutes
#        self.timer.start(5000) # update every 5 seconds

    def update_temperature(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            request = requests.get('http://api.wunderground.com/api/2690ba4d103ecbaf/conditions/q/pws:KMAMEDWA4.json')
        except requests.packages.urllib3.exceptions.NewConnectionError:
            print('Connection failed: Max retries exceeded')
            return
        except TimeoutError:
            print('Connection failed: Timeout')
            return
        except Exception as e:
            print(f'Exception requesting data @ {timestamp}: {e}')
            self.update_log(f'Exception requesting data @ {timestamp}: {e}\n')
            return
        
        try:
            self.temperature_f = json.loads(request.text)['current_observation']['temp_f']
        except json.decoder.JSONDecodeError:
            print(f'Malformed JSON returned @ {timestamp}')
            return
        except Exception as e:
            print(f'Exception decoding data: {e}')
            self.update_log(f'Exception decoding data @ {timestamp}: {e}\n')
            return

        self.update_log(timestamp + '\t%.1f°F\n' % self.temperature_f)
            
        print(timestamp + '\t%.1f°F' % self.temperature_f)
        final_image_size = 32
        scale_factor = 5
        big_image_size = (final_image_size*scale_factor, final_image_size*scale_factor)
        image = Image.new("RGBA", big_image_size, (10,10,10))
        draw = ImageDraw.Draw(image)
        fontsize = int(final_image_size*scale_factor/1.3)
        font = ImageFont.truetype(r'C:\Windows\Fonts\calibrib.ttf', fontsize)
        txt = '%.0f' % self.temperature_f
        draw.text((18, final_image_size*scale_factor/5.5), txt, (255,255,255), font=font)
        img_resized = image.resize((final_image_size, final_image_size), Image.ANTIALIAS)
        
        img_resized.save('temperature.png')
        
        self.setIcon(QtGui.QIcon('temperature.png'))
        self.setToolTip('%.1f°F: ' % self.temperature_f + timestamp)

    def update_log(self, text):
        with open(self.logfpath, 'a') as logfile:
            logfile.write(text)
    

def main():
    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(QtGui.QIcon('blank.png'), w)
    tray_icon.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
