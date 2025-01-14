#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 2022-04-25

from PyQt5 import QtGui, QtCore, QtWidgets
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from scipy.fftpack import rfft, irfft, fftfreq
import numpy as np
import time
from math import log10

import opbox_visa as opcard_lib




class Plot(QtWidgets.QDialog):
    def __init__(self, parent=None, background_color='#336799', text_color='color: white'):
        QtWidgets.QDialog.__init__(self, parent)

        self.time = [0,0]

        self.block_measurement = False
        self.markers_fft = ()
        self.fft_filt_marker = ()
        
        #------------------------------------------------------------------------------ plot

        self.sc = MyStaticMplCanvas(width=5, height=4, dpi=100)
        self.sc.figure.set_facecolor(background_color)

        self.mouse = (0,0)
        self.mouse_click = (0,0)
        self.gain_value = 36.
        
        # plot
        self.sc_fft = MyStaticMplCanvas(width=5, height=4, dpi=100, xlabel="f, MHz", ylable="")
        self.sc_fft.figure.set_facecolor(background_color)
        #self.sc.new_plot(self.my_instrument.t_us, self.env)
        
        
        #------------------------------------------------------------------------------ Selection

        list0 = ("none", "fft","fftw", "fft-filtr", "Gain")
        self.fft = Selection(selection_list=list0, text_color=text_color)
        #QtCore.QObject.connect(self.fft, QtCore.SIGNAL("go"), self.change_fft) # PyQt4
        
        #------------------------------------------------------------------------------ velocity
                     
        self.velocity = DoubleData("velocity, m/s", 1456.0, text_color=text_color, box_type="H")
        self.velocity.data.setMaximum(50000)

        list0 = (u"μs", "mm", "in")
        self.velocity_list = Selection(text="", selection_list=list0, text_color=text_color, box_type="H")

        self.box_velocity = QtWidgets.QHBoxLayout()
        self.box_velocity.addWidget(self.velocity)
        self.box_velocity.addWidget(self.velocity_list)
        #self.box_velocity.setMargin(50)
        #self.box_velocity.setSpacing(50)

        #------------------------------------------------------------------------------ gain function

        self.__gain_function = QtWidgets.QLineEdit()
        self.__gain_function.hide()
        self.button_gain_set = QtWidgets.QPushButton("set")
        self.button_gain_set.hide()
        #QtCore.QObject.connect(self.button_gain_set, QtCore.SIGNAL("clicked()"), self.gain_function_set)
        self.button_gain_set.clicked.connect( self.gain_function_set )

        self.boxgain_h = QtWidgets.QHBoxLayout()
        self.boxgain_h.addWidget(self.__gain_function)
        self.boxgain_h.addWidget(self.button_gain_set)
                
        #------------------------------------------------------------------------------ settings

        self.boxfft_h = QtWidgets.QHBoxLayout()
        self.boxfft_h.addWidget(self.sc_fft)
        self.boxfft_h.addWidget(self.fft)

        self.boxfft = QtWidgets.QVBoxLayout()
        self.boxfft.addLayout( self.boxfft_h )
        self.boxfft.addLayout( self.boxgain_h )        

        #------------------------------------------------------------------------------ tabs

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("background-color: #336799")
        
        tab_fft	= QtWidgets.QWidget()
        self.tabs.addTab(tab_fft,"fft")
        tab_fft.setLayout(self.boxfft)

        tab_chart = QtWidgets.QWidget()
        self.tabs.addTab(tab_chart,"Chart")
        #tab_chart.setLayout(self.boxfft)

        tab_scaner = QtWidgets.QWidget()
        self.tabs.addTab(tab_scaner,"Scaner")
        #tab_scaner.setLayout(self.boxfft)

        tab_encoders = QtWidgets.QWidget()
        self.tabs.addTab(tab_encoders,"Encoders")
        #tab_encoders.setLayout(self.boxfft)

        tab_parameters= QtWidgets.QWidget()
        self.tabs.addTab(tab_parameters,"Parameters")
        #tab_parameters.setLayout(self.boxfft)

        #------------------------------------------------------------------------------ type

        # Add subject ID text field
        self.subject_id = QtWidgets.QLineEdit()
        self.subject_id.setStyleSheet("background-color: white")
        self.subject_id.setMaximumWidth(100)
        subject_label = QtWidgets.QLabel("Subject ID:")
        subject_label.setStyleSheet("color: white")

        # Add tooth ID dropdown (1-32)
        self.tooth_id = QtWidgets.QComboBox(self)
        self.tooth_id.setStyleSheet("background-color: white")
        self.tooth_id.setMaximumWidth(100)
        self.tooth_id.addItems([f"{i}" for i in range(1, 33)])
        tooth_label = QtWidgets.QLabel("Tooth ID:")
        tooth_label.setStyleSheet("color: white")

        # Add site ID dropdown (1-6)
        self.site_id = QtWidgets.QComboBox(self)
        self.site_id.setStyleSheet("background-color: white")
        self.site_id.setMaximumWidth(100)
        self.site_id.addItems([f"{i}" for i in range(1, 7)])
        site_label = QtWidgets.QLabel("Site ID:")
        site_label.setStyleSheet("color: white")

        # Original type measurement dropdown
        list0 = ("RF", "ABS", "POSITIVE", "NEGATIVE", "ENVELOPE")
        self.type_measurement = QtWidgets.QComboBox(self)
        self.type_measurement.setStyleSheet("background-color: white")
        self.type_measurement.setMaximumWidth(100)
        self.type_measurement.addItems(list0)

        # Labels
        tooth_label = QtWidgets.QLabel("Tooth ID:")
        tooth_label.setStyleSheet("color: white")

        site_label = QtWidgets.QLabel("Site ID:")
        site_label.setStyleSheet("color: white")
        self.subject_id = QtWidgets.QLineEdit()
        self.subject_id.setStyleSheet("background-color: white")
        self.subject_id.setMaximumWidth(100)
        subject_label = QtWidgets.QLabel("Subject ID:")
        subject_label.setStyleSheet("color: white")

        # Layout
        self.hboxset = QtWidgets.QHBoxLayout()
        self.hboxset.addSpacing(10)
        self.hboxset.addWidget(subject_label)
        self.hboxset.addWidget(self.subject_id)
        self.hboxset.addSpacing(20)
        self.hboxset.addWidget(tooth_label)
        self.hboxset.addWidget(self.tooth_id)
        self.hboxset.addSpacing(20)
        self.hboxset.addWidget(site_label)
        self.hboxset.addWidget(self.site_id)
        self.hboxset.addSpacing(20)
        self.hboxset.addWidget(self.type_measurement)
        #------------------------------------------------------------------------------

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addLayout(self.hboxset)
        self.vbox.addWidget(self.sc)
        self.vbox.addLayout(self.box_velocity)
        self.vbox.addWidget(self.tabs)
                        
        self.setLayout(self.vbox)
        

    def plot_fft(self, time, data):

        if self.fft.selection.currentText() == "fftw":
            if self.sc.markers_fft != ():
                dt = time[1]-time[0]
                data_cut = data[int(self.sc.markers_fft[0][0]/dt):int(self.sc.markers_fft[0][1]/dt)]
                f_signal = rfft(data_cut)
                W = fftfreq(len(data_cut), d=abs(dt*2.))

                self.sc_fft.new_plot(W, abs(f_signal), xlim=[0,20], argmax=f_signal[2:].argmax()+2)
            else:
                return 1
            
        elif self.fft.selection.currentText() == "fft":
            f_signal = rfft(data)
            W = fftfreq(len(data), d=abs((time[1]-time[0])*2.))

            self.sc_fft.new_plot(W, abs(f_signal), xlim=[0,20], argmax=f_signal[2:].argmax()+2)

        elif self.fft.selection.currentText() == "fft-filtr":
            f_signal = rfft(data)
            W = fftfreq(len(data), d=abs((time[1]-time[0])*2.))

            if self.sc_fft.markers_fft==():
                self.sc_fft.markers_fft_show = True
                self.sc_fft.markers_fft = np.array([[5,15],[0.5*f_signal.max(),0.5*f_signal.max()]])

            if self.fft.selection.currentText() != "none":            
                self.sc_fft.new_plot(W, abs(f_signal), xlim=[0,20])
            else:
                self.sc_fft.new_plot([0.,10.,20.], [0.,0.,0.], xlim=[0,20])
                
        return 0

        
        

    def on_off(self, time, data, mode_pe_tt="PE", point_to_show = [], marker=()):

        self.plot_fft(time, data)

        if self.velocity_list.selection.currentText() == "mm":
            time = 1.e-3*self.velocity.data.value() * time
            self.sc.xlabel = "S, mm"

            if mode_pe_tt == "PE":
                time = time/2.

        elif self.velocity_list.selection.currentText() == "in":
            time = 0.0393700787*1.e-3*self.velocity.data.value() * time
            self.sc.xlabel = "S, in"

            if mode_pe_tt == "PE":
                time = time/2.

            
        else:
            self.sc.xlabel = "t, $\mu$s"

        
        if self.fft.selection.currentText() == "fftw":
            self.sc_fft.markers_fft_show = False
            self.sc.markers_fft_show = True
            if self.sc.markers_fft == ():
                self.sc.markers_fft = np.array([[0.3,0.7],[0.5,0.5]])
                self.sc.markers_fft[0] *= time.max()
                self.sc.markers_fft[1] *= data.max()
        else:
            self.sc.markers_fft_show = False
            self.sc_fft.markers_fft_show = False

        if self.fft.selection.currentText() == "fft-filtr":
            self.sc_fft.markers_fft_show = True
            self.sc.markers_fft_show = False
            f_signal = rfft(data)
            W = fftfreq(len(data), d=abs((time[1]-time[0])*2.))

            self.cut_f_signal =  f_signal.copy()
            self.cut_f_signal[(W < self.sc_fft.markers_fft[0][0] )] = 0
            self.cut_f_signal[(W > self.sc_fft.markers_fft[0][1] )] = 0

            self.sc_fft.markers_fft[1] = [0.5*f_signal.max(),0.5*f_signal.max()]

            data = irfft(self.cut_f_signal)
        else:
            self.sc_fft.markers_fft_show = False

        #if self.fft.selection.currentText() == "none":
            #self.sc_fft.new_plot([0.,10.,20.], [0.,0.,0.], xlim=[0,20])
            
            
		
        
        if self.type_measurement.currentText() in ["ABS", "POSITIVE", "ENVELOPE", "NEGATIVE"]:
            #self.sc.new_plot(time, data, point_to_show=point_to_show, marker=marker, xlim=(time[0], time[-1]), ylim=(0.,0.5))
            self.sc.new_plot(time, data, point_to_show=point_to_show, marker=marker, xlim=(time[0], time[-1]))
        #elif self.type_measurement.currentText() == "NEGATIVE":
            #self.sc.new_plot(time, data, point_to_show=point_to_show, marker=marker, xlim=(time[0], time[-1]), ylim=(-0.5,0.))
        else:
            self.sc.new_plot(time, data, point_to_show=point_to_show, marker=marker, xlim=(time[0], time[-1]), ylim=(-0.5,0.5))
            #self.sc.new_plot(time, data)
            #self.sc.new_plot(time, data, point_to_show=point_to_show, marker=marker)

        self.mouse = self.sc.mouse
        self.mouse_click = self.sc.mouse_click

        if self.sc.block_measurement == False:
            self.block_measurement = False
        else:
            self.block_measurement = True

        
        self.time = time
        self.data = data


    def gain_function_set(self):
        gain_function = "self.gain_function = %s" % (self.__gain_function.text().replace("t", "self.time"))
        #code = compile(gain_function, '<string>', 'exec')
        #exec( code )

        #for i in range(len(self.gain_function)):
        #    if self.gain_function[i] > 65:
        #        self.gain_function[i] = 65
        #    if self.gain_function[i] < -31:
        #        self.gain_function[i] = -31
        
        """self.sc_fft.new_plot(self.time, self.gain_function)

        for i in range(len(self.gain_function)):
            self.gain_function[i] = int(8.+(self.gain_function[i]+31.)/(31.+65.)*(200.-8.))"""
        
        #self.emit( QtCore.SIGNAL("gain_function_set") )
        ##QtCore.QObject.connect(self.on_off, QtCore.SIGNAL("clicked()"), self.gain_function_set)
        ##QtCore.QObject.connect(self.punkt1, QtCore.SIGNAL("go"), self.go1)


    def change_fft(self):
        if self.fft.selection.currentText() == "Gain":
            self.__gain_function.show()
            self.button_gain_set.show()
        else:
            self.__gain_function.hide()
            self.button_gain_set.hide()
    
                

class Buttons(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        #------------------------------------------------------------------------------ Button

        self.on_off = QtWidgets.QPushButton("off")
        self.on_off.setStyleSheet("background-color: red")
        self.on_off.clicked.connect(self.color_on_off)

        self.collect_data = QtWidgets.QPushButton("Collect Samples")
        font = self.collect_data.font()
        font.setBold(True)
        self.collect_data.setFont(font)
        
        self.load = QtWidgets.QPushButton("Load")
        
        self.save = QtWidgets.QPushButton("Save")

        self.quit = QtWidgets.QPushButton("&Quit")
        
        #------------------------------------------------------------------------------

        self.vbox = QtWidgets.QHBoxLayout()
        self.vbox.addWidget(self.on_off)
        self.vbox.addWidget(self.collect_data)
        self.vbox.addWidget(self.load)
        self.vbox.addWidget(self.save)
        self.vbox.addWidget(self.quit)
                
        self.setLayout(self.vbox)

    def color_on_off(self, on_off_status = 0):

        if on_off_status:
            self.on_off.setStyleSheet("background-color: green")
            self.on_off.setText("on")
        else:
            self.on_off.setStyleSheet("background-color: red")
            self.on_off.setText("off")

    
    
        
    


    


class Settings(QtWidgets.QDialog):
    def __init__(self, parent=None, text_color='color: white', deviceNr='USB0::0x0547::0x1003::SN_24.99::RAW'):
        QtWidgets.QDialog.__init__(self, parent)

        #------------------------------------------------------------------------------

        self.setMaximumWidth(220)
        self.setMinimumWidth(220)

        #------------------------------------------------------------------------------

        self.point_to_show = []
        self.offset_value = 0
        self.delay_Ts = 0
        self.marker = ()

        #------------------------------------------------------------------------------ errorMessageDialog

        self.errorMessageDialog = QtWidgets.QErrorMessage(self)
        
        #------------------------------------------------------------------------------ opcard
        
        self.opbox_on(deviceNr=deviceNr)
                
        #------------------------------------------------------------------------------ Selection

        list0 = ("Level %s" % i for i in range(17))
        self.level = Selection(text="Pulse Voltage", selection_list=list0, text_color=text_color)
        self.level.selection.setCurrentIndex(15)
        self.level.selection.activated.connect(self.change_level)

        list0 = ("TT", "PE")
        self.mode_pe_tt = Selection(text="Mode PE/TT", selection_list=list0, text_color=text_color)
        self.mode_pe_tt.selection.setCurrentIndex(1)
        self.mode_pe_tt.selection.activated.connect(self.change_mode_pe_tt)

        list0 = ("%s MHz" % i for i in (100,50,33.3,25,20,16.7,14.3,12.5,11.1,10,9.1,8.3,7.7,7.1,6.7))
        self.sampling_frequency = Selection(text="Sampling Frequency [MHz]", selection_list=list0, text_color=text_color)
        self.sampling_frequency.selection.activated.connect(self.change_sampling_frequency)

        list0 = ['0.5 - 6MHz', '1 - 6MHz', '2 - 6MHz', '4 - 6MHz']
        list0.extend( ["%s - 10MHz" %i for i in (0.5,1,2,4)] )
        list0.extend( ["%s - 15MHz" %i for i in (0.5,1,2,4)] )
        list0.extend( ["%s - 25MHz" %i for i in (0.5,1,2,4)] )
        self.analog_filters = Selection(text="Change analog filters [MHz]", selection_list=list0, text_color=text_color)
        self.analog_filters.selection.setCurrentIndex(1)
        self.analog_filters.selection.activated.connect(self.change_analog_filters)

        list0 = ("0 dB", "+24 dB", "-20 dB")
        self.pre_amplifier = Selection(text="Pre-amplifier", selection_list=list0, text_color=text_color)
        self.pre_amplifier.selection.setCurrentIndex(0)
        self.pre_amplifier.selection.activated.connect(self.change_pre_amplifier)

        list0 = ("Constant", "TGC")
        self.gain_mode = Selection(text="Gain Mode", selection_list=list0, text_color=text_color)
        self.gain_mode.selection.activated.connect(self.change_gain_mode)

        list0 = ("off",)
        self.avarage = Selection(text="Avarage", selection_list=list0, text_color=text_color)
        self.avarage.selection.activated.connect(self.change_avarage)

        list0 = ("Internal (SW)", "External x", "External y", "Timer PRF", "Encoder A", "Encoder B")
        self.trigger = Selection(text="Tigger", selection_list=list0, text_color=text_color)
        self.trigger.selection.activated.connect(self.change_trigger)

        list0 = ("off",)
        self.counter_mode = Selection(text="Counter Mode", selection_list=list0, text_color=text_color)
        self.counter_mode.selection.activated.connect(self.change_counter_mode)



        #------------------------------------------------------------------------------ DoubleData

        self.pulse_widht = DoubleData("Pulse Widht [us]", 3.1, text_color=text_color)
        self.pulse_widht.data.setMaximum(6.3)
        #QtCore.QObject.connect(self.pulse_widht.data, QtCore.SIGNAL("valueChanged(double)"), self.change_pulse_widht) # PyQt4
        self.pulse_widht.data.valueChanged.connect( self.change_pulse_widht )

        self.gain = DoubleData("Gain (constant) [dB]", 36, text_color=text_color)
        self.gain.data.setMaximum(65)
        self.gain.data.setMinimum(-31)
        self.gain.data.setSingleStep(0.5)
        #QtCore.QObject.connect(self.gain.data, QtCore.SIGNAL("valueChanged(double)"), self.change_gain) # PyQt4
        self.gain.data.valueChanged.connect( self.change_gain )

        self.delay = DoubleData("Delay", 0, text_color=text_color)
        self.delay.data.setMaximum(100000000000)
        ##QtCore.QObject.connect(self.delay.data, QtCore.SIGNAL("valueChanged(double)"), self.change_delay) # PyQt4
        self.delay.data.valueChanged.connect( self.change_delay )

        self.window = DoubleData("Window", 100., text_color=text_color)
        self.window.data.setMaximum(2680)
        self.window.data.setMinimum(1)
        ###QtCore.QObject.connect(self.window.data, QtCore.SIGNAL("valueChanged(double)"), self.change_window) # PyQt4
        self.window.data.valueChanged.connect( self.change_window )
        
        self.prf = 0.8
        self.prf_doubledata = DoubleData("PRF [kHz]", self.prf, text_color=text_color)
        ###QtCore.QObject.connect(self.prf.data, QtCore.SIGNAL("valueChanged(double)"), self.change_prf) # PyQt4
        self.prf_doubledata.data.valueChanged.connect( self.change_prf )

               
        #------------------------------------------------------------------------------

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.addWidget(self.level)
        self.vbox.addWidget(self.pulse_widht)
        self.vbox.addWidget(self.mode_pe_tt)
        self.vbox.addWidget(self.sampling_frequency)
        self.vbox.addWidget(self.analog_filters)
        self.vbox.addWidget(self.pre_amplifier)
        self.vbox.addWidget(self.gain_mode)
        self.vbox.addWidget(self.gain)
        self.vbox.addWidget(self.avarage)
        self.vbox.addWidget(self.delay)
        self.vbox.addWidget(self.window)
        self.vbox.addWidget(self.trigger)
        self.vbox.addWidget(self.counter_mode)
        self.vbox.addWidget(self.prf_doubledata)


        #------------------------------------------------------------------------------ cursor

        self.cursor_on_off = CheckBox_on_off("ON/OFF Measurment")
        #QtCore.QObject.connect(self.cursor_on_off, QtCore.SIGNAL("go"), self.change_cursor_on_off)

        #------------------------------------
        
        list0 = ("Auto", "Markers")
        self.cursor_type = QtWidgets.QComboBox(self)
        #self.connect(self.cursor_type, QtCore.SIGNAL('activated(QString)'), self.go)
        self.cursor_type.setStyleSheet("background-color: white")
        #self.connect(self.cursor_type, QtCore.SIGNAL('activated(QString)'), self.set_display_cursors)
        
        self.cursor_type.addItems(list0)

        #------------------------------------

        
        list0 = ("SOFT", "HARD")
        self.soft_hard = QtWidgets.QComboBox(self)
        self.soft_hard.setStyleSheet("background-color: white")

        self.soft_hard.addItems(list0)

        list0 = ("REL", "ABS")
        self.rel_abs = QtWidgets.QComboBox(self)
        self.rel_abs.setStyleSheet("background-color: white")

        self.rel_abs.addItems(list0)

        self.boxcursor_soft_rel = QtWidgets.QHBoxLayout()
        self.boxcursor_soft_rel.addWidget(self.soft_hard)
        self.boxcursor_soft_rel.addWidget(self.rel_abs)

        #------------------------------------


        list0 = ("MAX", "LEVEL", "RISING", "FALLING", "TRANSITION")
        self.cursor_type_measurement = QtWidgets.QComboBox(self)
        self.cursor_type_measurement.setStyleSheet("background-color: white")

        self.cursor_type_measurement.addItems(list0)

        

        #------------------------------------

        self.keep_order = CheckBox_on_off("keep order")
        

        #------------------------------------

        self.offset = DoubleData("offset", 0.00, text_color=text_color, box_type="H")
        #QtCore.QObject.connect(self.offset, QtCore.SIGNAL("go"), self.change_offset)
        self.offset.data.setSingleStep(0.1)
        #self.pulse_widht.data.setMaximum(6.3)

        #------------------------------------

        self.cursors_measurement_list = []

        color = ("green","#2EFEF7","yellow")
        for j in range(3):
            for i in ("TIM%s" % j,"AMP%s" % j, "ATT%s" % j):
                if i[:3] == "TIM":
                    self.cursors_measurement_list.append( Text_double_checkBox_on_off(i, background_color = "background-color: %s" % color[j]) )
                else:
                    self.cursors_measurement_list.append( DoubleData_no_go(data_name=i, box_type="H", background_color = "background-color: %s" % color[j]) )
                                        

        for i in ("T2-T1","T3-T1","T3-T2", "AMP2-AMP1","AMP3-AMP1","AMP3-AMP2", "ATT2-ATT1","ATT3-ATT1","ATT3-ATT2"):
            self.cursors_measurement_list.append( DoubleData_no_go(data_name=i, box_type="H", background_color = "background-color: white" ))

        #self.connect(self.cursors_measurement_list[0].check_1, QtCore.SIGNAL('stateChanged(int)'), self.set_display_cursors)
        #self.connect(self.cursors_measurement_list[3].check_1, QtCore.SIGNAL('stateChanged(int)'), self.set_display_cursors)

        
        #[i.setStyleSheet('font-size: 8pt; font-family: Courier;') for i in self.cursors_measurement_list]
        #[i.data.setStyleSheet('font-size: 8pt; font-family: Courier;') for i in self.cursors_measurement_list]

        self.cursor_type.currentIndexChanged['QString'].connect(self.clear_display_cursors)
                        
        #------------------------------------

        self.boxcursor = QtWidgets.QVBoxLayout()
        self.boxcursor.setSpacing(0)
        self.boxcursor.addWidget(self.cursor_on_off)
        self.boxcursor.addWidget(self.cursor_type)
        self.boxcursor.addLayout(self.boxcursor_soft_rel)
        self.boxcursor.addWidget(self.cursor_type_measurement)
        self.boxcursor.addWidget(self.keep_order)
        self.boxcursor.addWidget(self.offset)
        [self.boxcursor.addWidget(i) for i in self.cursors_measurement_list]
                
        #------------------------------------------------------------------------------ tabs

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("background-color: #336799")
        
        tab_settings	= QtWidgets.QWidget()
        self.tabs.addTab(tab_settings,"Settings")
        tab_settings.setLayout(self.vbox)

        tab_cursors	= QtWidgets.QWidget()
        self.tabs.addTab(tab_cursors,"Cursors")
        tab_cursors.setLayout(self.boxcursor)
        

        tab_mux	= QtWidgets.QWidget()
        self.tabs.addTab(tab_mux,"Mux")
        #tab_cursors.setLayout(self.vbox)

        self.vbox_all = QtWidgets.QVBoxLayout()
        self.vbox_all.addWidget(self.tabs)
        
                
        self.setLayout(self.vbox_all)


        self.freq = float(self.sampling_frequency.selection.currentText()[:-3])
        self.t = 1./(self.freq)
        n = int( self.window.data.value()/self.t )

        self.time = np.arange(0,n*self.t,self.t)
        self.cursor_on_off_value = self.cursor_on_off.check_1.checkState()

        #----------------------------------------------------
        
        self.change_sampling_frequency()
        self.change_pulse_widht()
        self.change_gain()
        self.change_window()
        self.change_prf()

        #----------------------------------------------------

    def opbox_on(self, deviceNr):
        try:
            self.opcard = opcard_lib.Opbox_v21(deviceNr=deviceNr)
        except:
            print("err: make self.opcard")
        
        try:     
            self.opcard.default_configuration()
        except:
            self.errorMessageDialog.showMessage("Device not found")


    def change_mode_pe_tt(self):
        if self.mode_pe_tt.selection.currentText() == "TT":
            if self.opcard.SetAnalogInput_TT() == 1:
                self.errorMessageDialog.showMessage("err TT")
                return 1

        if self.mode_pe_tt.selection.currentText() == "PE":
            if self.opcard.SetAnalogInput_PE() == 1:
                self.errorMessageDialog.showMessage("err PE")
                return 1


    def change_level(self):
        if self.opcard.SetPulseVoltage_level_stop_run(int(self.level.selection.currentText()[6:])) != 0:
            self.errorMessageDialog.showMessage("err level")
            return 1

    def change_sampling_frequency(self):
        self.freq = float(self.sampling_frequency.selection.currentText()[:-3])
        self.t = 1./(self.freq)
        if self.opcard.SetSamplingFreq( self.sampling_frequency.selection.currentIndex()+1 ) != 0:
            self.errorMessageDialog.showMessage("err sampling frequency")
            return 1
        


    def change_analog_filters(self):
        if self.opcard.SetAnalogFilters( self.analog_filters.selection.currentIndex() ) != 0:
            self.errorMessageDialog.showMessage("err analog filters")
            return 1
        

    def change_pre_amplifier(self):
        print( self.pre_amplifier.selection.currentIndex() )
        if self.opcard.SetAttenHilo( self.pre_amplifier.selection.currentIndex() ) != 0:
            self.errorMessageDialog.showMessage("err pre amplifier")
            return 1
            
    def change_gain_mode(self):
        
        if self.opcard.SetGainMode( self.gain_mode.selection.currentIndex() ) != 0:
            self.errorMessageDialog.showMessage("err gain mode")
            return 1 

    def change_avarage(self):
        pass

    def change_trigger(self):
        pass

    def hange_counter_mode(self):
        pass

    def change_counter_mode(self):
        pass

    def change_pulse_widht(self):
        if self.opcard.SetTimePulse_stop_run( self.pulse_widht.data.value() ) != 0:
            self.errorMessageDialog.showMessage("err pulse widht")
            return 1
        

    def change_gain(self):
        #print(self.gain.data.value())
        value = self.gain.data.value()
        self.gain_value = round(2*self.gain.data.value())/2.
        
        #print(self.gain_value)
        self.gain.data.setValue(self.gain_value)
        if self.opcard.SetConstGain( self.gain_value ) != 0:
            self.errorMessageDialog.showMessage("err change gain")
            return 1
        
    def change_delay(self):

        t =1./(float(self.sampling_frequency.selection.currentText()[:-3]))
        
        #self.delay_Ts_old = self.delay_Ts*t
        #self.delay_Ts = int(0.01*self.delay.data.value()/t)
        self.delay_Ts = int(self.delay.data.value()/t)
                
        #print(self.delay_Ts)
        

        if self.opcard.SetDelay( self.delay_Ts ) != 0:
            self.errorMessageDialog.showMessage("err change delay")
            return 1

        if self.cursor_type.currentText() == "Markers":
            if self.rel_abs.currentText() == "REL":
                if self.marker != ():
                    self.marker[0][0] += self.delay.data.value() - self.delay_Ts_old
                    self.marker[0][1] += self.delay.data.value() - self.delay_Ts_old

                    if len(self.marker[0])>2:
                        self.marker[0][2] += self.delay.data.value() - self.delay_Ts_old
                        self.marker[0][3] += self.delay.data.value() - self.delay_Ts_old

                    if len(self.marker[0])>4:
                        self.marker[0][4] += self.delay.data.value() - self.delay_Ts_old
                        self.marker[0][5] += self.delay.data.value() - self.delay_Ts_old
        

    def change_window(self):

        
        self.freq = float(self.sampling_frequency.selection.currentText()[:-3])


        self.t = 1./(self.freq)
        n = int( self.window.data.value()/self.t )
                
        self.time = np.arange(0,n*self.t,self.t)
                
        if self.opcard.SetBufferDepth( n ) != 0:
            self.errorMessageDialog.showMessage("err pre amplifier")
            return 1
        

    def change_prf(self):
        self.prf = self.prf_doubledata.data.value()


    def change_offset(self):
        self.offset_value = self.offset.data.value()


    def change_cursor_on_off(self):
        self.cursor_on_off_value = self.cursor_on_off.check_1.checkState()



    def set_time(self):
        self.freq = float(self.sampling_frequency.selection.currentText()[:-3])
        
        self.t = 1./(self.freq)
        self.n = len(self.opcard.data)
        
        self.time = self.delay.data.value() + np.arange(0,self.n*self.t,self.t)


    def clear_display_cursors(self):
        [self.cursors_measurement_list[i].data.display( 0. ) for i in range(len(self.cursors_measurement_list))]


    def set_display_cursors(self):
        
        if self.cursor_type.currentText() == "Markers":
            self.cursors_measurement_list[0].check_1.setEnabled(True)

            if self.cursors_measurement_list[0].check_1.checkState():
                self.cursors_measurement_list[3].check_1.setEnabled(True)
            
                if self.cursors_measurement_list[3].check_1.checkState():
                    self.cursors_measurement_list[6].check_1.setEnabled(True)
                else:
                    self.cursors_measurement_list[6].check_1.setEnabled(False)

            else:
                self.cursors_measurement_list[3].check_1.setEnabled(False)
                self.cursors_measurement_list[6].check_1.setEnabled(False)
            
        else:
            self.cursors_measurement_list[0].check_1.setEnabled(False)
            self.cursors_measurement_list[3].check_1.setEnabled(False)
            self.cursors_measurement_list[6].check_1.setEnabled(False)


    
    def cursors(self, mouse=(), mouse_click=(), marker_range=()):

        offset_value = int(float(self.offset_value)/self.t)
                
        if self.cursor_on_off_value:
            if self.cursor_type.currentText() == "Auto":
                if self.cursor_type_measurement.currentText() == "MAX":

                    self.point_to_show = []
                    self.marker = ()

                    try:
                        self.point_to_show = ( self.opcard.data_argmax, self.opcard.data_argmax1 )
                    except:
                        print( "err argmax" )
                    
                    try:
                        tim_value1 = round((self.delay_Ts+self.opcard.data_argmax)*self.t, 2)
                        tim_value2 = round((self.delay_Ts+self.opcard.data_argmax1)*self.t, 2)
                        amp_value1 = round( self.opcard.data_max, 2)
                        amp_value2 = round( self.opcard.data_max1, 2)
                    except:
                        print( "err value1" )

                    try:
                        if amp_value1 != 0:
                            att_value1 = round(self.gain_value + 20.*log10(abs(amp_value1/0.5)), 2)
                        else:
                            att_value1 = 0

                        if amp_value1 != 0:
                            att_value2 = round(self.gain_value + 20.*log10(abs(amp_value2/0.5)), 2)
                        else:
                            att_value1 = 0
                            
                    except:
                        print( "err auto value att" )


                    try:
                        dtime21 = round(tim_value2 - tim_value1, 2)
                        amp21 = round(amp_value2 - amp_value1, 2)
                        att21 = round(att_value2 - att_value1, 2)
                    except:
                        print( "err value2" )
                        

                    try:
                        self.cursors_measurement_list[0].data.display( tim_value1 )
                        self.cursors_measurement_list[1].data.display( amp_value1 )
                        self.cursors_measurement_list[2].data.display( att_value1 )
                        self.cursors_measurement_list[3].data.display( tim_value2 )
                        self.cursors_measurement_list[4].data.display( amp_value2 )
                        self.cursors_measurement_list[5].data.display( att_value2 )
                        self.cursors_measurement_list[9].data.display( dtime21 )
                        self.cursors_measurement_list[12].data.display( amp21 )
                        self.cursors_measurement_list[15].data.display( att21 )
                    except:
                        print( "err show value" )

                else:
                    self.point_to_show = []


            

                    
            elif self.cursor_type.currentText() == "Markers":


                self.point_to_show = []
                
                tim_value1 = round((self.delay_Ts+self.opcard.data_argmax)*self.t, 2)
                tim_value2 = round((self.delay_Ts+self.opcard.data_argmax1)*self.t, 2)

                if self.cursors_measurement_list[0].check_1.checkState():

                    if self.marker == ():
                        self.marker = [[tim_value1,tim_value2],[self.opcard.data_max*0.9,self.opcard.data_max*0.9]]
                    else:
                        pass

                    if self.cursors_measurement_list[3].check_1.checkState():
                        if len(self.marker[0]) == 2:
                            self.marker[0].extend([tim_value1,tim_value2])
                            self.marker[1].extend([self.opcard.data_max*0.7,self.opcard.data_max*0.7])

                        if self.cursors_measurement_list[6].check_1.checkState():
                            if len(self.marker[0]) == 4:
                                self.marker[0].extend([tim_value1,tim_value2])
                                self.marker[1].extend([self.opcard.data_max*0.5,self.opcard.data_max*0.5])

                        else:
                            if len(self.marker[0]) == 6:
                                self.marker[0] = self.marker[0][:4]
                                self.marker[1] = self.marker[1][:4]
                    else:
                        if len(self.marker[0]) == 4:
                            self.marker[0] = self.marker[0][:2]
                            self.marker[1] = self.marker[1][:2]

                        
                

                    if marker_range != ():
                        if self.cursor_type_measurement.currentText() == "MAX":

                            try:
                                tmax = [int(marker_range[i])+self.opcard.data[int(marker_range[i]):int(marker_range[i+1])].argmax() for i in range(0, len(marker_range), 2) if int(marker_range[i])<int(marker_range[i+1])]
                                
                                for i in range(0, len(marker_range), 2):

                                    if int(marker_range[i]) > int(marker_range[i+1]):
                                        tmax.append( int(marker_range[i+1])+self.opcard.data[int(marker_range[i+1]):int(marker_range[i])].argmax() )
                                    
                                    if int(marker_range[i])==int(marker_range[i+1]):
                                        tmax.append(int(marker_range[i]))

                                
                                for i in range(len( tmax )):
                                    if tmax[i] <  0:
                                        tmax[i] = 0
                                    if tmax[i] >  self.n:
                                        tmax[i] = self.n
                                        

                                self.point_to_show = ( tmax )
                            except:
                                print( "err marker tmax" )
                                #return 1

                            try:                                
                                time = np.array([ round( self.time[tmax[i]], 2 ) for i in range(len(tmax))])
                            except:
                                print( "err marker time" )
                                #return 1


                            try:
                                amp = np.array([ round( self.opcard.data[tmax[i]], 2 ) for i in range(len(tmax))])
                            except:
                                print( "err marker amp" )
                                #return 1

                            try:
                                att = np.array([ round( self.gain_value + 20.*log10(abs(i/0.5)), 2 ) if i!=0 else 0 for i in amp])
                            except:
                                print( "err marker att" )
                                #att = np.array([ round( self.gain_value + 20.*log10(abs(i/0.5)), 2 ) if i!=0 else 0 for i in amp])
                                #return 1


                            try:                                
                                if len(tmax) == 1:
                                    [self.cursors_measurement_list[i].data.display( 0. ) for i in range(3,18)]
                            except:
                                print( "err tmax==1" )
                                return 1

                            try:
                                [self.cursors_measurement_list[3*i].data.display( time[i] ) for i in range(len(time)) if isinstance(time[i], float)]
                                [self.cursors_measurement_list[3*i+1].data.display( amp[i] ) for i in range(len(amp)) if isinstance(amp[i], float)]
                                [self.cursors_measurement_list[3*i+2].data.display( att[i] ) for i in range(len(att)) if isinstance(att[i], float)]
                            except:
                                print( "err marker display" )
                                return 1


                            try:                                                                        
                                if len(tmax) >= 2:                                    
                                    self.cursors_measurement_list[9].data.display( round(time[1]-time[0], 2) )
                                    self.cursors_measurement_list[12].data.display( round(amp[1]-amp[0], 2) )
                                    self.cursors_measurement_list[15].data.display( round(att[1]-att[0], 2) )
                            except:
                                print( "err tmax==2" )
                                #return 1


                            try:                                                                        
                                if len(time) >= 3:
                                    self.cursors_measurement_list[10].data.display( round(time[2]-time[0], 2) )
                                    self.cursors_measurement_list[13].data.display( round(amp[2]-amp[0], 2) )
                                    self.cursors_measurement_list[16].data.display( round(att[2]-att[0], 2) )

                                    self.cursors_measurement_list[11].data.display( round(time[2]-time[1], 2) )
                                    self.cursors_measurement_list[14].data.display( round(amp[2]-amp[1], 2) )
                                    self.cursors_measurement_list[17].data.display( round(att[2]-att[1], 2) )
                                
                            except:
                                print( "err tmax=3" )
                                #return 1


                            


                            
                                                        
                            

                else:
                    self.point_to_show = []
                    self.marker = ()

                    
                    

            else:
                self.point_to_show = []
                self.marker = ()
                                       
                            

        else:
            self.point_to_show = []
            self.marker = ()
                    
    

    


class Selection(QtWidgets.QDialog):
    def __init__(self, parent=None, text="", selection_list=(""), text_color='color: white', box_type="V"):
        QtWidgets.QDialog.__init__(self, parent)

                
        text = QtWidgets.QLabel(text)
        text.setStyleSheet(text_color)
                
        self.selection = QtWidgets.QComboBox(self)
        self.selection.setMinimumHeight(15)
        #self.connect(self.selection, QtCore.SIGNAL('activated(QString)'), self.go)
        self.selection.setStyleSheet("background-color: white")

        self.selection_list = selection_list

        for i in self.selection_list:
            self.selection.addItem(i)

        if box_type=="V":
            self.vbox = QtWidgets.QVBoxLayout()
        else:
            self.vbox = QtWidgets.QHBoxLayout()

        if text != "":
            self.vbox.addWidget(text)
            
        self.vbox.addWidget(self.selection)
                		
        self.setLayout(self.vbox)

        

    


class DoubleData(QtWidgets.QWidget):

    def __init__(self, data_name="", start_data=0.0, text_color='color: white', box_type="V", background_color = "background-color: white"):      
        super(DoubleData, self).__init__()

        if box_type=="V":
            self.box = QtWidgets.QVBoxLayout()
        else:
            self.box = QtWidgets.QHBoxLayout()
        
        self.data_text = QtWidgets.QLabel(data_name, self)
        self.data_text.setMinimumHeight(15)
        self.data_text.setStyleSheet(text_color)
        self.data = QtWidgets.QDoubleSpinBox(self)
        self.data.setMinimumHeight(15)
        self.data.setStyleSheet(background_color)
        self.data.setMinimum(0)
        self.data.setMaximum(5000000000)
        self.data.setValue(start_data)
              

        #-------------------------------------------------------------

        self.box.setSpacing(0)
        self.box.addWidget(self.data_text)
        self.box.addWidget(self.data)
        
        
        self.setLayout(self.box)

    

class DoubleData_no_go(QtWidgets.QWidget):

    def __init__(self, data_name="", start_data=0.0, text_color='color: white', box_type="V", background_color = "background-color: white"):      
        super(DoubleData_no_go, self).__init__()

        if box_type=="V":
            self.box = QtWidgets.QVBoxLayout()
        else:
            self.box = QtWidgets.QHBoxLayout()
        
        self.data_text = QtWidgets.QLabel(data_name, self)
        self.data_text.setStyleSheet(text_color)
        #self.data = QtWidgets.QDoubleSpinBox(self)
        self.data = QtWidgets.QLCDNumber(self)
        self.data.setMinimumHeight(15)
        self.data.setStyleSheet(background_color)
        self.data.setMaximumHeight(20)
        self.data.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        
        
        #self.data.setMinimum(0)
        #self.data.setMaximum(5000000000)
        #self.data.setValue(start_data)
        self.data.display(start_data)
        ##QtCore.QObject.connect(self.data, QtCore.SIGNAL("valueChanged(double)"), self.go)
        

        #-------------------------------------------------------------
        
        self.box.addWidget(self.data_text)
        self.box.addWidget(self.data)
        self.box.addSpacing(25)
        
        
        self.setLayout(self.box)







class CheckBox_on_off(QtWidgets.QWidget):

    def __init__(self, name,  text_color='color: white'):      
        super(CheckBox_on_off, self).__init__()

        
        self.box = QtWidgets.QHBoxLayout()
        self.dana_text = QtWidgets.QLabel(name, self)
        self.dana_text.setStyleSheet(text_color)

        self.check_1 = QtWidgets.QCheckBox()
                
      
        self.box.addWidget(self.check_1)
        self.box.addWidget(self.dana_text)
                
        self.setLayout(self.box)

    
        


class Text_double_checkBox_on_off(QtWidgets.QWidget):

    def __init__(self, data_name="", start_data=0.0, text_color='color: white', background_color = "background-color: white"):      
        super(Text_double_checkBox_on_off, self).__init__()

        self.data_text = QtWidgets.QLabel(data_name, self)
        self.data_text.setStyleSheet(text_color)
        
        self.data = QtWidgets.QLCDNumber(self)
        self.data.setMinimumHeight(15)
        self.data.setStyleSheet(background_color)
        self.data.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.data.setMaximumHeight(20)
        #self.data.setMinimum(0)
        #self.data.setMaximum(5000000000)
        self.data.display(start_data)
        
        
        self.check_1 = QtWidgets.QCheckBox()
        self.check_1.setEnabled(False)
        
        self.box = QtWidgets.QHBoxLayout()      
        
        self.box.addWidget(self.data_text)
        self.box.addSpacing(42)
        self.box.addWidget(self.data)
        self.box.addWidget(self.check_1)
        
                
        self.setLayout(self.box)

    


#----------------------------------------------------------------

        

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100, xlabel="t, $\mu$s", ylable="U"):

        self.block_measurement = False

        self.mouse = (0,0)
        self.mouse_click = (0,0)
        self.xlabel = xlabel
        self.ylable = ylable
        self.marker_move = ()
        self.marker_range = ()
        self.markers_fft = ()
        self.markers_fft_show = False
        
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
      

              
        #self.axes.hold(True)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        #FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        
        cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        cid = self.fig.canvas.mpl_connect('button_release_event', self.onclick)
        cid = self.fig.canvas.mpl_connect('motion_notify_event', self.onmove)
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        

    def onclick(self, event):
        #print( 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(event.button, event.x, event.y, event.xdata, event.ydata) )

        try:
            if self.marker_move == ():
                self.mouse_click = (event.xdata, event.ydata)
                self.marker_move = self.idn
            else:
                self.marker_move = ()
                self.block_measurement = False
        except:
            print( "err onclick" )
            return 1
        

    def onmove(self, event):
        #print( 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(event.button, event.x, event.y, event.xdata, event.ydata))

        try:
            if isinstance(event.xdata, float) and isinstance(event.ydata, float):
                self.mouse = (event.xdata, event.ydata)
            else:
                self.mouse = (0., 0., 0.)
               
            
        except:
            print( "err mouse 0" )
            return 1

        if self.marker_move != ():

            if self.mouse[0]>self.tmin and self.mouse[0]<self.tmax:

                if self.markers_fft != ():
                        if self.marker == ():
                            self.markers_fft[0][self.marker_move] = self.mouse[0]
                            self.markers_fft[1][self.marker_move] = self.mouse[1]


                            if self.marker_move%2:
                                try:
                                    self.markers_fft[1][self.marker_move-1] = self.mouse[1]
                                except:
                                    print( "err plot fft mouse 2" )
                                    return 1
                            else:
                                try:
                                    self.markers_fft[1][self.marker_move+1] = self.mouse[1]
                                except:
                                    print( "err plot fft mouse 3" )
                                    return 1

                        
                        

                if self.marker != ():

                    try:
                        self.marker[0][self.marker_move] = self.mouse[0]
                        self.marker[1][self.marker_move] = self.mouse[1]
                    except:
                        print( "err plot mouse 1" )
                        return 1

                    if self.marker_move%2:
                        try:
                            self.marker[1][self.marker_move-1] = self.mouse[1]
                        except:
                            print( "err plot mouse 2" )
                            return 1
                    else:
                        try:
                            self.marker[1][self.marker_move+1] = self.mouse[1]
                        except:
                            print( "err plot mouse 3" )
                            return 1

                    

            
            


    def onpick(self, event):
        pass
        

    #def mouse_move(self):
        #print( "a" )

        

    def compute_initial_figure(self):
        pass

    


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def compute_initial_figure(self):
        t = np.arange(0.0, 3.0, 0.01) #[0.01*i for i in range(0,300)]#arange(0.0, 3.0, 0.01)
        s = np.sin(4*t) #[0.01*i for i in range(0,300)]#arange(0.0, 3.0, 0.01)
        self.axes.plot(t, s)
        self.axes.grid(True)

        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylable)


    def onpick(self, event):
        try:
            self.block_measurement = True
            ind = event.ind
            #print( help(event) )
            self.idn = ind[0]
            #print( self.idn )
            
        except:
            print( "err onpick" )
            return 1        
        
        
    def new_plot(self, t, s, xlim="", ylim="", point_to_show=[], marker=(), argmax=-1):

        self.tmin = t.min()
        self.tmax = t.max()
        self.marker = marker
        
        self.axes.cla()
        self.axes.plot(t, s)
        #self.axes.set_autoscaley_on(False)

        color = ("green","#2EFEF7","yellow")
        if len(point_to_show) != 0:
            [self.axes.plot(t[point_to_show[i]], s[point_to_show[i]], 'ro', color=color[i]) for i in range(len(point_to_show))]
            
        self.axes.grid(True)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylable)
                
        if xlim != "":
            self.axes.set_xlim(xlim)
            self.axes.set_autoscaley_on(False)

        if ylim != "":
            self.axes.set_ylim(ylim)
            
        
        if marker != (): # and len(self.mouse)<3:

            try:
                [self.axes.plot(marker[0][i:i+2], marker[1][i:i+2], '-o', color=color[i/2]) for i in range(0,len(marker[0]),2)]

                try:
                    if self.markers_fft_show:
                        self.axes.scatter(marker[0], marker[1], picker=True)
                        #self.axes.scatter(self.markers_fft[0], self.markers_fft[1], picker=True)
                        self.axes.plot(self.markers_fft[0], self.markers_fft[1], '-o', color="red")                        
                    else:
                        self.axes.scatter(marker[0], marker[1], picker=True)
                    
                except:
                    print( "err plot mouse picker" )

                try:
                    self.marker_range = [int(len(t)*(i-self.tmin)/(self.tmax-self.tmin)) for i in self.marker[0]]
                except:
                    print( "err plot mouse marker range" )

            except:
                print( "err plot marker" )
                #return 1

        #elif self.marker != ():
            #[self.axes.plot(marker[0][i:i+2], marker[1][i:i+2], '-o', color=color[i/2]) for i in range(0,len(marker[0]),2)]

        #if self.markers_fft != ():
        if self.markers_fft_show:
            if self.marker == ():
                
                self.axes.plot(self.markers_fft[0], self.markers_fft[1], '-o', color="red")
                self.axes.scatter(self.markers_fft[0], self.markers_fft[1], picker=True)
                
        if argmax > 0:
            self.axes.text(t[argmax]+1, 0.9*s[argmax], u'f = %sMHz' % round(t[argmax], 2))
            
            
        self.draw()

        

        

    def new_plot_od_czasu(self, t, s, xlabel="t, us", ylable="U, V"):
        self.axes.set_xlabel("a")
        self.axes.set_ylabel("b")
        self.axes.plot_date(t, s)
        self.axes.grid(True)
        
        self.draw()

    #def mouseMoveEvent(self, event):      
        #self.xx=event.pos().x()
        #self.yy=event.pos().y()
        #self.update()

        
    #def mouseReleaseEvent(self, event):
        
        #print( self.xx, self.yy )
    

    





# main
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)	
    #icon = Settings()
    icon = Buttons()
    icon.show() 			
    app.exec_()  
