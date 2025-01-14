#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 2022-04-25

class Trigger():
    value0 = 0b00000000
    value1 = 0b00000111
    value = '%s%s' % (chr(value0),chr(value1))
    
    TriggerSource = 0b0000
    TriggerEnable = 0b0
    TriggerReset = 0b0
    TriggerSw = 0b0
    
    XY_Divider_Enable = 0b1
    XY_Divider_Reset = 0b1
    TimeEnable = 0b1
    Trigger_Status = 0b0
    Trigger_Overrun_Status = 0b0

    def setValue(self):
        self.value0 = (0<<7) + (self.TriggerSw<<6) + (self.TriggerReset<<5) + (self.TriggerEnable<<4) + self.TriggerSource
        self.value1 = (0<<7) + (self.Trigger_Overrun_Status<<6) + (0<<5) + (self.Trigger_Status<<4) + (0<<3) + (self.TimeEnable<<2) + (self.XY_Divider_Reset<<1) + self.XY_Divider_Enable
        self.value = '%s%s' % (chr(self.value0),chr(self.value1))



class Measure():
    value0 = 0b00000000
    value1 = 0b00000000
    value = '%s%s' % (chr(value0),chr(value1))
    
    SamplingFreq = 0b0000
    GainMode = 0b00
    DataProcessingMode = 0b0
    StoreDisable = 0b0

    def setValue(self):
        self.value0 = (self.DataProcessingMode<<7) + (0<<6) + (self.GainMode<<4) + self.SamplingFreq
        self.value1 = (0b00000<<3) + (self.StoreDisable<<2) + (0<<1) + self.DataProcessingMode
        self.value = '%s%s' % (chr(self.value0),chr(self.value1))


class AnalogCtrl():
    value0 = 0b00000000
    value1 = 0b00000000
    value = '%s%s' % (chr(value0),chr(value1))
    
    AnalogFilter = 0b0000
    InputAttenuator = 0b0
    PostAmplifier = 0b0
    AnalogInput = 0b0

    def setValue(self):
        self.value0 = (0<<7) + (self.AnalogInput<<6) + (self.PostAmplifier<<5) + (self.InputAttenuator<<4) + self.AnalogFilter
        self.value1 = 0b00000000
        self.value = '%s%s' % (chr(self.value0),chr(self.value1))
    
        

  
