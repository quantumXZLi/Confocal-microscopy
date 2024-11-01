import sys
from gui_plot3 import Ui_Form

from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRectF
import matplotlib.pyplot as plt
import numpy as np
import io
from scipy.optimize import curve_fit


def lorentz( x, x0, amp, width,back):
    return amp*(.5*width)/((x-x0)**2+(.5*width)**2)+back

def LFit (filename,pguess = (-1,-1,-1,.01), scaling =500):
    #scaling = 500 #MHz/mV
    format_plot()
    xData ,yData = np.load(filename)
    popt, pcov = curve_fit(lorentz, xData, yData, p0 = pguess)
    plt.plot(xData,yData)
    plt.plot(xData,lorentz(xData,popt[0],popt[1],popt[2],popt[3]))
    print(popt[0],popt[1],popt[2],popt[3])
    print ("the linewdith is", popt[2]*scaling , "MHz")
    return popt


def format_plot():
    fig= plt.gcf()
    fig.set_size_inches(6,4.5)
    plt.rcParams['font.size'] = 10.5


class MainWindow(QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.scene = QGraphicsScene(self)
        self.graphicsView_2.setScene(self.scene)
        
        self.load_wave.clicked.connect(self.add_wavescan)
        self.load_mode.clicked.connect(self.add_modescan)
        self.modeup.clicked.connect(self.mode_up)
        self.modedown.clicked.connect(self.mode_down)
        self.waveup.clicked.connect(self.wave_up)
        self.wavedown.clicked.connect(self.wave_down)


    def add_wavescan(self):
        # Generate a simple plot

        index = int(self.wavescan.text())
        index= f"{index:03}"
        string = "wavescan"+str(index)
        x,y=np.load(string+".npy")
        plt.figure()
        format_plot()
        plt.plot(x, y)

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a QPixmap from the buffer
        image = QPixmap()
        image.loadFromData(buf.getvalue())

        # Add the QPixmap to the QGraphicsScene
        self.scene.addPixmap(image)


    def add_modescan(self):
        # Generate a simple plot

        index = int(self.modescan.text())
        index= f"{index:03}"
        string = "modescan"+str(index)
        x,y=np.load(string+".npy")
        plt.figure()
        format_plot()
        plt.plot(x, y)

        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a QPixmap from the buffer
        image = QPixmap()
        image.loadFromData(buf.getvalue())

        # Add the QPixmap to the QGraphicsScene
        self.scene.addPixmap(image)

    def mode_up(self):
        # Generate a simple plot

        index = int(self.modescan.text())
        index = index+1

        self.modescan.setText(str(index))
        self.add_modescan()


    def mode_down(self):
        # Generate a simple plot
        index = int(self.modescan.text())
        index = index-1

        self.modescan.setText(str(index))
        self.add_modescan()

    def wave_up(self):
        # Generate a simple plot

        index = int(self.wavescan.text())
        index = index+1

        self.wavescan.setText(str(index))
        self.add_wavescan()


    def wave_down(self):
        # Generate a simple plot
        index = int(self.wavescan.text())
        index = index-1

        self.wavescan.setText(str(index))
        self.add_wavescan()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
