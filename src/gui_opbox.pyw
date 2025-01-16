#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 2022-04-25

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import time
import numpy as np
import h5py
from pathlib import Path
import os
import pyvisa
import threading
#import multiprocessing, time, signal
from numpy import savetxt
from datetime import datetime
from matplotlib import pyplot

import gui_secondary


def find_usb_raw_resource():
    """
    Find the USB RAW resource address from NI-VISA.
    Returns the first USB RAW resource found or None if not found.
    """
    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources("?*")
        
        # Look for our specific device
        for resource in resources:
            if ("USB" in resource and 
                "RAW" in resource and 
                "0x0547" in resource and # vendor ID
                "0x1003" in resource): # product ID
                return resource
                
        print("No matching USB RAW resource found")
        return None
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None
    finally:
        # Clean up
        if 'rm' in locals():
            rm.close()


class Gui_opcard(QtWidgets.QDialog):
       
    def __init__(self, parent=None, deviceNr=find_usb_raw_resource()):
        QtWidgets.QDialog.__init__(self, parent)


        #------------------------------------------------------------------------------
        self.hardware_ID = deviceNr
        self.on_off_d = False
        self.fname = "."

        #------------------------------------------------------------------------------ color
        self.background_color = '#336799'
        text_color='color: white'
        
        pal=QtGui.QPalette()
        role = QtGui.QPalette.Background
        pal.setColor(role, QtGui.QColor(self.background_color))
        self.setPalette(pal)
        
        #------------------------------------------------------------------------------ plot

        self.sc = gui_secondary.Plot(background_color=self.background_color, text_color='color: white')
        
        #------------------------------------------------------------------------------ settings

        self.settings = gui_secondary.Settings(text_color='color: white', deviceNr=deviceNr)

        #------------------------------------------------------------------------------ buttons

        self.buttons = gui_secondary.Buttons()
        self.buttons.quit.clicked.connect(self.close)
        self.buttons.collect_data.clicked.connect(self.collect_pulses)
        
        #------------------------------------------------------------------------------ connect

        #QtCore.QObject.connect(self.buttons.on_off, QtCore.SIGNAL("clicked()"), self.on_off) # PyQt4
        self.buttons.on_off.clicked.connect(self.on_off)

        #------------------------------------------------------------------------------ box and setLayout

        self.plotbox = QtWidgets.QVBoxLayout()
        self.plotbox.addWidget(self.sc)
        
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addLayout(self.plotbox)
        self.hbox.addWidget(self.settings)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.buttons)
                
        self.setLayout(self.vbox)

        #------------------------------------------------------------------------------ box and setLayout
        


    def __del__(self):
        self.timer.stop()
        

    def on_off(self):
        
        if self.on_off_d:
            self.on_off_d = False
            self.buttons.color_on_off(self.on_off_d)
            self.timer.stop()
            
                                    
        else:
            self.on_off_d = True
            self.buttons.color_on_off(self.on_off_d)

            self.timer = QtCore.QTimer()
            #QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.on_off_r) # old pyqt4
            self.timer.timeout.connect(self.on_off_r)
            self.timer.start(50)



    def on_off_r(self):
        
            try:
                self.settings.opcard.ack_trigger_and_one_read__offset(self.settings.offset_value, self.sc.type_measurement.currentText())
            except:
                print( "err opcard" )


            try:
                self.settings.set_time()
            except:
                print( "err calc time" )

            try:
                self.settings.cursors(mouse=self.sc.mouse, mouse_click=self.sc.mouse_click, marker_range=self.sc.sc.marker_range)
                
            except:
                print( "err cursors" )
            
            try:
                self.sc.block_measurement = True
                self.sc.on_off(time=self.settings.time,data=self.settings.opcard.data, mode_pe_tt=self.settings.mode_pe_tt.selection.currentText(), point_to_show=self.settings.point_to_show, marker = self.settings.marker)
            except:
                print( "err plot", sys.exc_info()[0] )



            
    

            
    def closeEvent(self, event):
        quit_msg = "Do You realy want to close the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        
        if reply == QtWidgets.QMessageBox.Yes:
            icon.on_off_d = False
            event.accept()
        else:
            event.ignore()


    def collect_pulses(self):
        """Collect 10 pulses and save to HDF5"""
        INTER_PULSE_INTERVAL = 50  # ms
        try:
            # Get values from UI
            subject_id = self.sc.subject_id.text()
            tooth_id = int(self.sc.tooth_id.currentText())
            site_id = int(self.sc.site_id.currentText())

            if not subject_id:
                QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a Subject ID")
                return

            sequence_data = []
            timestamps = []

            # Show progress dialog
            progress = QtWidgets.QProgressDialog("Collecting pulses...", None, 0, 10, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            
            # Get sampling frequency:
            sampling_freq = float(self.settings.sampling_frequency.selection.currentText().replace(" MHz", ""))

            
            for i in range(10):
                progress.setValue(i)
                QtWidgets.QApplication.processEvents()  # Keep GUI responsive
                
                # Acquire single pulse
                self.settings.opcard.ack_trigger_and_one_read__offset(
                    self.settings.offset_value, 
                    self.sc.type_measurement.currentText()
                )
                sequence_data.append(np.array(self.settings.opcard.data))
                timestamps.append(datetime.now().timestamp())
                
                if i < 9:  
                    time.sleep(INTER_PULSE_INTERVAL / 1000)  # Convert ms to seconds

            progress.setValue(10)
            
            # Get path to save data:
            cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            # Go up one level to root, then into data
            data_dir = os.path.join(cur_dir.parent,"data")
            # Create the data directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)

            # Create the full path for your file
            timestamp_str = datetime.now().strftime('%Y%m%d') # Note that this will 
            filename = f"{subject_id}_{timestamp_str}.h5"
            save_path = os.path.join(data_dir, filename)
            with h5py.File(save_path, 'a') as f:
                # Create/get tooth group
                tooth_group = f.require_group(f"tooth_{tooth_id:02d}")
                
                # Create/get site group
                site_group = tooth_group.require_group(f"site_{site_id}")
                
                # Calculate time axis
                t = np.arange(0, len(sequence_data[0])) / sampling_freq

                # Store datasets, overwrite if they already exist
                if 'waveforms' in site_group:
                    del site_group['waveforms']
                if 'timestamps' in site_group:
                    del site_group['timestamps']
                if 'time' in site_group:
                    del site_group['time']
                    
                site_group.create_dataset('waveforms', data=np.array(sequence_data))
                site_group.create_dataset('timestamps', data=np.array(timestamps))
                site_group.create_dataset('time', data=t)
                
                # Store metadata:
                site_group.attrs['acquisition_time'] = datetime.now().isoformat()
                site_group.attrs['sampling_rate'] = self.settings.sampling_frequency.selection.currentText()
                site_group.attrs['interval_ms'] = INTER_PULSE_INTERVAL
                site_group.attrs['gain'] = self.settings.gain.data.value()
                site_group.attrs['pre_amplifier'] = self.settings.pre_amplifier.selection.currentText()
                site_group.attrs['pulse_width_us'] = self.settings.pulse_widht.data.value()
                site_group.attrs['tooth_id'] = tooth_id
                site_group.attrs['site_id'] = site_id

            QtWidgets.QMessageBox.information(self, "Success", 
                f"Successfully saved 10 pulses to {filename}\nTooth: {tooth_id}, Site: {site_id}")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error collecting data: {str(e)}")

            

     
        



# main
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = Gui_opcard()
    icon.setWindowTitle("Opbox")
    icon.setFixedSize(1024,763)
    icon.show()
    #icon.showMaximized()
    #icon.showFullScreen()
    app.exec_()

    
    
