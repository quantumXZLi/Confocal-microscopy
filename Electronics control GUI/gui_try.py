import sys
from PyQt5.QtWidgets import QApplication, QMainWindow,QPushButton, QLineEdit, QLabel,QDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import *
import os.path
import time
from wanglib.instruments import signal_generators
from operator import attrgetter
import pyvisa 
from wanglib.instruments.signal_generators import ag8648, rigol, sgs100a
from wanglib.instruments.tektronix import TDS3000, Tek7104
from scipy.optimize import curve_fit
from wanglib.instruments.lockins2 import srs844
import matplotlib as mpl
from circa.expt import gen_gated_counts
from time import sleep
from toptica.lasersdk.dlcpro.v2_2_0 import DLCpro, NetworkConnection
from toptica.lasersdk.client import Client, NetworkConnection
DLCPRO_CONNECTION = '128.223.23.108'




rm = pyvisa.ResourceManager()

rigol_b = rm.open_resource('USB0::0x1AB1::0x099C::DSG8M223900097::INSTR')
#rigol_t = rm.open_resource('USB0::0x1AB1::0x099C::DSG8M223900103::INSTR')
keysight = rm.open_resource('GPIB0::17::INSTR')
li = rm.open_resource("GPIB0::8::INSTR")

redpower_old = rm.open_resource("GPIB::18")
redpower_new = rm.open_resource("GPIB::19")



def set_phase2(to):
    cmd = ":SOURCE2:PHASE:ADJUST %.4f %s" % (to,"DEG")
    AFG_old.write(cmd)
    
def set_phase1(to):

    cmd = ":SOURCE1:PHASE:ADJUST %.4f %s" % (to,"DEG")
    AFG_old.write(cmd)
    
def set_AFGold_freq1(to):
    cmd =":SOURce1:FREQuency:FIXed %.7f %s" % (to,"MHz")
    AFG_old.write(cmd)
    
def set_AFGold_freq2(to):
    cmd =":SOURce2:FREQuency:FIXed %.7f %s" % (to,"MHz")
    AFG_old.write(cmd)
    
def set_AFGold_power1(to):
    cmd =":SOURce1:VOLTage:LEVel:IMMediate:AMPLitude %.2f%s" % (to,"Vpp")
    AFG_old.write(cmd)
    
def set_AFGold_power2(to):
    cmd =":SOURce2:VOLTage:LEVel:IMMediate:AMPLitude %.2f%s" % (to,"Vpp")
    AFG_old.write(cmd)
    
def state_AFGold_1(to):
    cmd = ":OUTPut1:STATe %d" % (to)
    AFG_old.write(cmd)
    
def state_AFGold_2(to):
    cmd = ":OUTPut2:STATe %d" % (to)
    AFG_old.write(cmd)


def set_AFGnew_level2(to):
    cmd =":SOURce2:VOLTage:LEVel:IMMediate:OFFSet %.4f%s" % (to,"V")
    AFG_new.write(cmd)


def smoothmove_laser(to):

    cur = client1.get('laser1:dl:pc:voltage-set')
    step = .1
    sign = 1 if (to > cur) else -1
    while abs(to - cur) > step:
        client1.set('laser1:dl:pc:voltage-set', cur + step*sign)
        cur = client1.get('laser1:dl:pc:voltage-set')
        sleep(0.1)
    client1.set('laser1:dl:pc:voltage-set', to)



def keysight_freq(to):

    keysight.write(":FREQ %s%s" %(to,"MHZ"))



def ask_AFGnew_level2():
    cmd = ":SOURce2:VOLTage:LEVel:IMMediate:OFFSet?"
    return float(AFG_new.query(cmd))




class Example(QMainWindow):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        key1 = QPushButton("keysight on", self)
        key1.setGeometry(30, 40, 140, 60)
        key1.setFont(QFont('Arial', 15))

        key0 = QPushButton("keysight off", self)
        key0.setGeometry(170, 40, 140, 60)
        key0.setFont(QFont('Arial', 15))
      
        key1.clicked.connect(self.keysight_on)            
        key0.clicked.connect(self.keysight_off)

        red_old1 = QPushButton("red old on", self)
        red_old1.setGeometry(30, 115, 140, 60)
        red_old1.setFont(QFont('Arial', 15))

        red_old0 = QPushButton("red old off", self)
        red_old0.setGeometry(170, 115, 140, 60)
        red_old0.setFont(QFont('Arial', 15))
      
        red_old1.clicked.connect(self.red_old_on)            
        red_old0.clicked.connect(self.red_old_off)


        red_new1 = QPushButton("red new on", self)
        red_new1.setGeometry(30, 190, 140, 60)
        red_new1.setFont(QFont('Arial', 15))

        red_new0 = QPushButton("red new off", self)
        red_new0.setGeometry(170, 190, 140, 60)
        red_new0.setFont(QFont('Arial', 15))
      
        red_new1.clicked.connect(self.red_new_on)            
        red_new0.clicked.connect(self.red_new_off)

        DC = QPushButton("show DC", self)
        DC.setGeometry(400, 40, 110, 40)
        DC.setFont(QFont('Arial', 15))
        DC.clicked.connect(self.show_DC)

        set_DC = QPushButton("set DC", self)
        set_DC.setGeometry(510, 40, 110, 40)
        set_DC.setFont(QFont('Arial', 15))
        set_DC.clicked.connect(self.set_DC)  

        self.DC_val = QLineEdit(self)
        self.DC_val.setFont(QFont('Arial', 15))        
        self.DC_val.setGeometry(400, 80, 80, 40) 

        self.DC_step = QLineEdit(self)
        self.DC_step.setFont(QFont('Arial', 15))        
        self.DC_step.setGeometry(480, 80, 70, 40)


        DC_1 = QPushButton('+', self)
        DC_1.setGeometry(550, 80, 40, 40) 
        DC_1.setFont(QFont('Arial', 15))
        DC_1.clicked.connect(self.DC_up)

        DC_2 = QPushButton('-', self)
        DC_2.setGeometry(590, 80, 40, 40) 
        DC_2.setFont(QFont('Arial', 15))
        DC_2.clicked.connect(self.DC_down)



        btn = QPushButton('Set Keysight amp', self)
        btn.setGeometry(30, 340, 170, 40)
        btn.clicked.connect(self.set_key_amp)
        btn.setFont(QFont('Arial', 15))

        btn2 = QPushButton('Set Keysight freq', self)
        btn2.setGeometry(210, 340, 170, 40)
        btn2.setFont(QFont('Arial', 15))
        btn2.clicked.connect(self.set_key_freq)


        btn_ask1 = QPushButton('ask K amp', self)
        btn_ask1.setGeometry(420, 340, 120, 35)
        btn_ask1.clicked.connect(self.ask_key_amp)
        btn_ask1.setFont(QFont('Arial', 15))

        btn2_ask2 = QPushButton('ask K freq', self)
        btn2_ask2.setGeometry(420, 375, 120, 35)
        btn2_ask2.setFont(QFont('Arial', 15))
        btn2_ask2.clicked.connect(self.ask_key_freq)

        
        self.key_amp = QLineEdit(self)
        self.key_amp.setGeometry(30, 380, 170, 30)
        self.key_amp.setFont(QFont('Arial', 15))
        
        self.key_freq = QLineEdit(self)
        self.key_freq.setFont(QFont('Arial', 15))
        self.key_freq.setGeometry(210, 380, 170, 30)       

        do_count = QPushButton("do count", self)
        do_count.setGeometry(400, 240, 110, 40)
        do_count.setFont(QFont('Arial', 15))
        do_count.clicked.connect(self.do_counts)



        self.counts = QLineEdit(self)
        self.counts.setGeometry(510, 240, 110, 40)
        self.counts.setFont(QFont('Arial', 15))

        self.step2_label = QLabel('step(MHZ)', self)
        self.step2_label.setFont(QFont('Arial', 15))
        self.step2_label.setGeometry(220, 290, 170, 40) 

        self.step2 = QLineEdit(self)
        self.step2.setGeometry(30, 290, 170, 40)
        self.step2.setFont(QFont('Arial', 15))



        rigol1 = QPushButton("rigol_t on", self)
        rigol1.setGeometry(400, 180, 110, 40)
        rigol1.setFont(QFont('Arial', 15))
        rigol0 = QPushButton("rigol_t off", self)
        rigol0.setGeometry(510, 180, 110, 40)
        rigol0.setFont(QFont('Arial', 15))
        rigol1.clicked.connect(self.rigol_t_on)            
        rigol0.clicked.connect(self.rigol_t_off)

        rigol1 = QPushButton("rigol_b on", self)
        rigol1.setGeometry(400, 135, 110, 40)
        rigol1.setFont(QFont('Arial', 15))
        rigol0 = QPushButton("rigol_b off", self)
        rigol0.setGeometry(510, 135, 110, 40)
        rigol0.setFont(QFont('Arial', 15))
        rigol1.clicked.connect(self.rigol_b_on)            
        rigol0.clicked.connect(self.rigol_b_off)

        btn_ri = QPushButton('Set rigol_b amp', self)
        btn_ri.setGeometry(30, 430, 170, 40)
        btn_ri.clicked.connect(self.set_ri_b_amp)
        btn_ri.setFont(QFont('Arial', 15))

        btn_ri2 = QPushButton('Set rigol_b freq', self)
        btn_ri2.setGeometry(210, 430, 170, 40)
        btn_ri2.clicked.connect(self.set_ri_b_freq)
        btn_ri2.setFont(QFont('Arial', 15))
        
        self.ri_b_amp = QLineEdit(self)
        self.ri_b_amp.setGeometry(30, 470, 170, 30)
        self.ri_b_amp.setFont(QFont('Arial', 15))        
        
        self.ri_b_freq = QLineEdit(self)
        self.ri_b_freq.setGeometry(210, 470, 170, 30)  
        self.ri_b_freq.setFont(QFont('Arial', 15))

        ri_ask1 = QPushButton('ask ri_b amp', self)
        ri_ask1.setGeometry(420, 430, 120, 35)
        ri_ask1.clicked.connect(self.ask_ri_b_amp)
        ri_ask1.setFont(QFont('Arial', 15))

        ri_ask2 = QPushButton('ask ri_b freq', self)
        ri_ask2.setGeometry(420, 465, 120, 35)
        ri_ask2.setFont(QFont('Arial', 15))
        ri_ask2.clicked.connect(self.ask_ri_b_freq)

        RI1 = QPushButton('+', self)
        RI1.setGeometry(385, 430, 35, 35) 
        RI1.setFont(QFont('Arial', 15))
        RI1.clicked.connect(self.up_RI_b_freq)

        RI2 = QPushButton('-', self)
        RI2.setGeometry(385, 465, 35, 35) 
        RI2.setFont(QFont('Arial', 15))
        RI2.clicked.connect(self.down_RI_b_freq)






        btn_ri = QPushButton('Set rigol_t amp', self)
        btn_ri.setGeometry(30, 820, 170, 40)
        btn_ri.clicked.connect(self.set_ri_t_amp)
        btn_ri.setFont(QFont('Arial', 15))

        btn_ri2 = QPushButton('Set rigol_t freq', self)
        btn_ri2.setGeometry(210, 820, 170, 40)
        btn_ri2.clicked.connect(self.set_ri_t_freq)
        btn_ri2.setFont(QFont('Arial', 15))
        
        self.ri_t_amp = QLineEdit(self)
        self.ri_t_amp.setGeometry(30, 860, 170, 30)
        self.ri_t_amp.setFont(QFont('Arial', 15))        
        
        self.ri_t_freq = QLineEdit(self)
        self.ri_t_freq.setGeometry(210, 860, 170, 30)  
        self.ri_t_freq.setFont(QFont('Arial', 15))

        ri_ask1 = QPushButton('ask ri_t amp', self)
        ri_ask1.setGeometry(420, 820, 120, 35)
        ri_ask1.clicked.connect(self.ask_ri_t_amp)
        ri_ask1.setFont(QFont('Arial', 15))

        ri_ask2 = QPushButton('ask ri_t freq', self)
        ri_ask2.setGeometry(420, 855, 120, 35)
        ri_ask2.setFont(QFont('Arial', 15))
        ri_ask2.clicked.connect(self.ask_ri_t_freq)

        RI1 = QPushButton('+', self)
        RI1.setGeometry(385, 820, 35, 35) 
        RI1.setFont(QFont('Arial', 15))
        RI1.clicked.connect(self.up_RI_t_freq)

        RI2 = QPushButton('-', self)
        RI2.setGeometry(385, 855, 35, 35) 
        RI2.setFont(QFont('Arial', 15))
        RI2.clicked.connect(self.down_RI_t_freq)







        btn_red_old = QPushButton('Set red_old amp', self)
        btn_red_old.setGeometry(30, 520, 170, 40) 
        btn_red_old.clicked.connect(self.set_red_old_amp)
        btn_red_old.setFont(QFont('Arial', 15))

        btn_red_new = QPushButton('Set red_new amp', self)
        btn_red_new.setGeometry(210, 520, 170, 40) 
        btn_red_new.setFont(QFont('Arial', 15))
        btn_red_new.clicked.connect(self.set_red_new_amp)
        
        self.red_new_amp = QLineEdit(self)
        self.red_new_amp.setGeometry(210, 560, 170, 30)
        self.red_new_amp.setFont(QFont('Arial', 15))         
        
        self.red_old_amp = QLineEdit(self)
        self.red_old_amp.setFont(QFont('Arial', 15))
        self.red_old_amp.setGeometry(30, 560, 170, 30) 


        r_ask1 = QPushButton('ask old amp', self)
        r_ask1.setGeometry(420, 520, 120, 35)
        r_ask1.clicked.connect(self.ask_old_amp)
        r_ask1.setFont(QFont('Arial', 15))

        r_ask2 = QPushButton('ask new amp', self)
        r_ask2.setGeometry(420, 555, 120, 35)
        r_ask2.setFont(QFont('Arial', 15))
        r_ask2.clicked.connect(self.ask_new_amp)        


        r_ask1 = QPushButton('set old f', self)
        r_ask1.setGeometry(420, 630, 120, 35)
        r_ask1.clicked.connect(self.set_old_f)
        r_ask1.setFont(QFont('Arial', 15))

        r_ask2 = QPushButton('set new f', self)
        r_ask2.setGeometry(420, 665, 120, 35)
        r_ask2.setFont(QFont('Arial', 15))
        r_ask2.clicked.connect(self.set_new_f)




        f_red_old = QPushButton('show red_old freq', self)
        f_red_old.setGeometry(30, 630, 170, 40) 
        f_red_old.setFont(QFont('Arial', 15))
        f_red_old.clicked.connect(self.show_red_old_freq)

        f_red_new = QPushButton('show red_new freq', self)
        f_red_new.setGeometry(210, 630, 180, 40) 
        f_red_new.setFont(QFont('Arial', 15))
        f_red_new.clicked.connect(self.show_red_new_freq)

        self.red_new_f = QLineEdit(self)
        self.red_new_f.setFont(QFont('Arial', 15))        
        self.red_new_f.setGeometry(210, 670, 180, 40) 
        
        self.red_old_f = QLineEdit(self)
        self.red_old_f.setFont(QFont('Arial', 15))        
        self.red_old_f.setGeometry(30, 670, 170, 40) 


        KEY1 = QPushButton('+', self)
        KEY1.setGeometry(385, 340, 35, 35) 
        KEY1.setFont(QFont('Arial', 15))
        KEY1.clicked.connect(self.up_KEY_freq)

        KEY2 = QPushButton('-', self)
        KEY2.setGeometry(385, 375, 35, 35) 
        KEY2.setFont(QFont('Arial', 15))
        KEY2.clicked.connect(self.down_KEY_freq)







        f_red_old1 = QPushButton('old +', self)
        f_red_old1.setGeometry(30, 710, 140, 40) 
        f_red_old1.setFont(QFont('Arial', 15))
        f_red_old1.clicked.connect(self.up_red_old_freq)

        f_red_old2 = QPushButton('old -', self)
        f_red_old2.setGeometry(30, 750, 140, 40) 
        f_red_old2.setFont(QFont('Arial', 15))
        f_red_old2.clicked.connect(self.down_red_old_freq)

        f_red_new1 = QPushButton('new +', self)
        f_red_new1.setGeometry(210, 710, 140, 40) 
        f_red_new1.setFont(QFont('Arial', 15))
        f_red_new1.clicked.connect(self.up_red_new_freq)

        f_red_new2 = QPushButton('new -', self)
        f_red_new2.setGeometry(210, 750, 140, 40) 
        f_red_new2.setFont(QFont('Arial', 15))
        f_red_new2.clicked.connect(self.down_red_new_freq)

        self.step_f = QLineEdit(self)
        self.step_f.setFont(QFont('Arial', 15))        
        self.step_f.setGeometry(420, 750, 100, 40)  

        self.step_label = QLabel('step size(laser)', self)
        self.step_label.setFont(QFont('Arial', 15))
        self.step_label.setGeometry(420, 710, 160, 40) 

        #self.step_label = QLabel('Fuck Physics', self)
        #self.step_label.setFont(QFont('Arial', 30))
        #self.step_label.setGeometry(30, 860, 350, 40)



        self.statusBar()
        
        self.setGeometry(340, 40, 640, 930)
        self.setWindowTitle('Electronics')
        self.show()



    def AFG_old1_off(self):
    	
        state_AFGold_1(0)
        self.success()

    def AFG_old1_on(self):
    	
        state_AFGold_1(1)
        self.success()

    def AFG_old2_on(self):
    	
        state_AFGold_2(1)
        self.success()

    def AFG_old2_off(self):
    	
        state_AFGold_2(0)
        self.success()


    def do_counts(self):
        
        gen = gen_gated_counts(t=0.5)
        _,rate = next(gen)
        self.counts.setText(str(round(rate,6)))



    def show_DC(self):
        
        DC=float(li.query("AUXO? 2"))
        self.DC_val.setText(str(DC))

    def set_DC(self):

        DC_now=self.DC_val.text()
        li.write("AUXO 2, %s" %str(DC_now))



    def DC_up(self):
        step=round(float(self.DC_step.text()),2)
        DC=round(float(self.DC_val.text()),2)
        li.write("AUXO 2, %s" %str(round((DC+step),2)))
        self.DC_val.setText(str(DC+step))

    def DC_down(self):
        
        step=round(float(self.DC_step.text()),2)
        DC=round(float(self.DC_val.text()),2)
        li.write("AUXO 2, %s" %str(round(DC-step,2)))
        self.DC_val.setText(str(DC-step))




    def AFG_old1_ask_amp(self):
        cmd =":SOURce1:VOLTage:LEVel:IMMediate:AMPLitude?"
        cur = float(AFG_old.query(cmd))
        cur = "{:.4f}".format(cur)
        self.AFG_old1_amp_val.setText(str(cur))


    def AFG_old1_ask_f(self):
        cmd = ":SOURce1:FREQuency:FIXed?"
        cur = float(AFG_old.query(cmd))*10**(-6)
        self.AFG_old1_f_val.setText(str(cur))     

    def AFG_old1_set_amp(self):
        tttt = self.AFG_old1_amp_val.text()
        set_AFGold_power1(float(tttt))


    def AFG_old1_set_f(self):
        tttt = self.AFG_old1_f_val.text()
        set_AFGold_freq1(float(tttt))  



    def up_KEY_freq(self):
        tttt = self.step2.text()
        cur = float(keysight.query(":FREQ?"))/1000000 
        new_cur = cur+float(tttt)
        keysight.write(":FREQ %s%s" %((new_cur),"MHZ"))
        self.key_freq.setText(str(new_cur))

    def down_KEY_freq(self):
        tttt = self.step2.text()
        cur = float(keysight.query(":FREQ?"))/1000000 
        new_cur = cur-float(tttt)
        keysight.write(":FREQ %s%s" %(new_cur,"MHZ"))
        self.key_freq.setText(str(new_cur))


    def down_RI_b_freq(self):
        tttt = self.step2.text()
        cur = float(rigol_b.query(":FREQ?"))/1000000
        new_cur = cur-float(tttt)
        rigol_b.write(":FREQ %s%s" %(new_cur,"MHZ"))
        self.ri_b_freq.setText(str(new_cur))

    def up_RI_b_freq(self):
        tttt = self.step2.text()
        cur = float(rigol_b.query(":FREQ?"))/1000000  
        new_cur = cur+float(tttt)
        rigol_b.write(":FREQ %s%s" %(new_cur,"MHZ"))
        self.ri_b_freq.setText(str(new_cur))



    def down_RI_t_freq(self):
        tttt = self.step2.text()
        cur = float(rigol_t.query(":FREQ?"))/1000000
        new_cur = cur-float(tttt)
        rigol_t.write(":FREQ %s%s" %(new_cur,"MHZ"))
        self.ri_t_freq.setText(str(new_cur))

    def up_RI_t_freq(self):
        tttt = self.step2.text()
        cur = float(rigol_t.query(":FREQ?"))/1000000  
        new_cur = cur+float(tttt)
        rigol_t.write(":FREQ %s%s" %(new_cur,"MHZ"))
        self.ri_t_freq.setText(str(new_cur))





    def up_red_old_freq(self):
        tttt = self.step_f.text()
        cur = ask_AFGnew_level2()
        new_cur = cur+float(tttt)
        smoothmove_ch2_AFG(new_cur)
        self.red_old_f.setText(str(new_cur))

    def down_red_old_freq(self):
        tttt = self.step_f.text()
        cur = ask_AFGnew_level2()  
        new_cur = cur-float(tttt)
        smoothmove_ch2_AFG(new_cur)
        self.red_old_f.setText(str(new_cur))

    def clear_all(self):
        self.key_freq.setText('null')
        self.key_amp.setText('null')        
        self.ri_freq.setText('null')
        self.ri_amp.setText('null')
        self.red_old_f.setText('null')
        self.red_new_f.setText('null')
        self.red_old_amp.setText('null')
        self.red_new_amp.setText('null')
        self.step_f.setText('0.002')        


    def ask_key_freq(self):
        cur = float(keysight.query(":FREQ?"))/1000000
        self.key_freq.setText(str(cur))


    def ask_ri_b_freq(self):
        cur = float(rigol_b.query(":FREQ?"))/1000000
        self.ri_b_freq.setText(str(cur))  

    def ask_ri_t_freq(self):
        cur = float(rigol_t.query(":FREQ?"))/1000000
        self.ri_t_freq.setText(str(cur))      


    def ask_key_amp(self):
        cur = float(keysight.query("POW:AMPL?"))
        self.key_amp.setText(str(cur))


    def ask_old_amp(self):
        cur = float(redpower_old.query("POW:AMPL?"))
        self.red_old_amp.setText(str(cur)) 


    def ask_new_amp(self):
        cur = float(redpower_new.query("POW:AMPL?"))
        self.red_new_amp.setText(str(cur))


    def ask_ri_b_amp(self):
        cur = float(rigol_b.query(":LEVEL?"))
        self.ri_b_amp.setText(str(cur))

    def ask_ri_t_amp(self):
        cur = float(rigol_t.query(":LEVEL?"))
        self.ri_t_amp.setText(str(cur))


    def set_new_f(self):

        tttt = self.red_new_f.text()
        smoothmove_laser(float(tttt))


    def set_old_f(self):
    	
        tttt = self.red_old_f.text()
        smoothmove_ch2_AFG(float(tttt))



    def up_red_new_freq(self):
        tttt = self.step_f.text()
        cur = client1.get('laser1:dl:pc:voltage-set')   
        new_cur = round(cur+float(tttt),4)
        smoothmove_laser(new_cur)
        self.red_new_f.setText(str(new_cur))    


    def down_red_new_freq(self):
        tttt = self.step_f.text()
        cur = client1.get('laser1:dl:pc:voltage-set')
        new_cur = round(cur-float(tttt),4)
        smoothmove_laser(new_cur)
        self.red_new_f.setText(str(new_cur))


    def show_red_new_freq(self):
		
        posi = round(client1.get('laser1:dl:pc:voltage-set'),4)
        self.red_new_f.setText(str(posi))

    def show_red_old_freq(self):
		
        posi = ask_AFGnew_level2()
        self.red_old_f.setText(str(posi))


    def success(self):
    	d = QDialog()
    	b1 = QPushButton("Done",d)
    	b1.clicked.connect(d.close)
    	b1.move(50,50)
    	d.setWindowTitle("status")
    	d.setWindowModality(Qt.ApplicationModal)
    	d.exec_()


    def set_key_amp(self):
        
        tttt = self.key_amp.text()
        keysight.write("POW:AMPL %.1f %s" % (float(tttt),"DBM"))
        self.success()


    def set_key_freq(self):
        
        tttt = self.key_freq.text()
        keysight_freq(float(tttt))
        self.success()

    def set_red_old_amp(self):
        
        tttt = self.red_old_amp.text()
        redpower_old.write("POW:AMPL %.1f %s" % (float(tttt),"DBM"))
        self.success()

    def set_red_new_amp(self):
        
        tttt = self.red_new_amp.text()
        redpower_new.write("POW:AMPL %.1f %s" % (float(tttt),"DBM"))
        self.success()

    def set_ri_b_amp(self):
        
        tttt = self.ri_b_amp.text()
        rigol_b.write(":LEVel %sdBm" % (tttt))
        self.success()

    def set_ri_b_freq(self):
        
        tttt = self.ri_b_freq.text()
        rigol_b.write(":FREQ %sMHz" % (tttt))
        self.success()


    def set_ri_t_amp(self):
        
        tttt = self.ri_t_amp.text()
        rigol_t.write(":LEVel %sdBm" % (tttt))
        self.success()

    def set_ri_t_freq(self):
        
        tttt = self.ri_t_freq.text()
        rigol_t.write(":FREQ %sMHz" % (tttt))
        self.success()

        
    def keysight_off(self):
      
        keysight.write("OUTP:STAT off")
        self.success()

    def keysight_on(self):
        
        keysight.write("OUTP:STAT on")
        self.success()


    def rigol_b_off(self):
        
        rigol_b.write("OUTP:STAT OFF")
        self.success()


    def rigol_b_on(self):
        
        rigol_b.write("OUTP:STAT ON")
        self.success()

    def rigol_t_off(self):
        
        rigol_t.write("OUTP:STAT OFF")
        self.success()


    def rigol_t_on(self):
        
        rigol_t.write("OUTP:STAT ON")
        self.success()


    def red_new_on(self):
    
        redpower_new.write("OUTP:STAT ON")
        self.success()


    def red_new_off(self):
    
        redpower_new.write("OUTP:STAT OFF")
        self.success()


    def red_old_on(self):
    
        redpower_old.write("OUTP:STAT ON")
        self.success()

    def red_old_off(self):
    
        redpower_old.write("OUTP:STAT OFF")
        self.success()		




        
def main():
    global client1
    with Client(NetworkConnection(DLCPRO_CONNECTION)) as client1:
        app = QApplication(sys.argv)
        ex = Example()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()