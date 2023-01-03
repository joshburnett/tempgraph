# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:03:10 2016
@author: Josh Burnett

Gets the current temperature for Milford, MA every five minutes and displays this in an icon in the system tray.
"""
#%%
import wx
import requests
import json
from PIL import Image, ImageDraw, ImageFont

class TaskBarApp(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, -1, title, size = (1, 1), style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.ICON_STATE = 1
        self.ID_ICON_TIMER=wx.NewId()
        self.tbicon = wx.TaskBarIcon()
        self.UpdateTemperature()

        self.tbicon.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnTaskBarRightClick)
        self.Bind(wx.EVT_TIMER, self.Log, id=self.ID_ICON_TIMER)
        self.SetIconTimer()
        self.Show(True)

    def OnTaskBarRightClick(self, evt):
        self.StopIconTimer()
        self.tbicon.Destroy()
        self.Close(True)
        wx.GetApp().ProcessIdle()

    def SetIconTimer(self):
        self.icontimer = wx.Timer(self, self.ID_ICON_TIMER)
        self.icontimer.Start(5000*60)

    def StartIconTimer(self):
        try:
            self.icontimer.Start(5000*60)
        except:
            pass

    def StopIconTimer(self):
        try:
            self.icontimer.Stop()
        except:
            pass

    def Log(self, evt):
        self.UpdateTemperature()
        print(u'%.1f°F' % self.temperature_f)
        
    def UpdateTemperature(self):
        self.temperature_f = json.loads(requests.get('http://api.wunderground.com/api/2690ba4d103ecbaf/conditions/q/pws:KMAMEDWA4.json').text)['current_observation']['temp_f']

        final_image_size = 32
        scale_factor = 5
        big_image_size = (final_image_size*scale_factor, final_image_size*scale_factor)
        image = Image.new("RGBA", big_image_size, (10,10,10))
        draw = ImageDraw.Draw(image)
        fontsize = int(final_image_size*scale_factor/1.3)
        font = ImageFont.truetype(r'C:\Windows\Fonts\calibrib.ttf', fontsize)
        txt = '%i' % self.temperature_f
        draw.text((18, final_image_size*scale_factor/5.5), txt, (255,255,255), font=font)
        img_resized = image.resize((final_image_size, final_image_size), Image.ANTIALIAS)
        
        img_resized.save('temperature.png')

        icon = wx.Icon('temperature.png', wx.BITMAP_TYPE_PNG)
        self.tbicon.SetIcon(icon, 'Current local temperature')

        
class MyApp(wx.App):
    def OnInit(self):
        frame = TaskBarApp(None, -1, ' ')
        frame.Center(wx.BOTH)
        frame.Show(False)
        return True

def main():
    app = MyApp(0)
    app.MainLoop()

if __name__ == '__main__':
    main()

