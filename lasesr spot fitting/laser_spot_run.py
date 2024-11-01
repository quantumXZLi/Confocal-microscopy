import sys
import io
from PyQt5.QtWidgets import QApplication, QLineEdit, QMainWindow, QPushButton, QGraphicsView, QGraphicsScene, QFileDialog,QMessageBox
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.optimize import curve_fit
from laser_spot import Ui_Laser


def get_line_coordinates(x0, y0, k, width=150, height=180):

    points=[]
    i=1
    x=int(x0)
    y=int(y0)
    while x<width and x>0 and y<height and y>0:
        points.append([x,y])        
        x=int(x0-i)
        y=int(y0-k*i)
        i=i+1
        
    i=1
    x=int(x0+i)
    y=int(y0+i)
    
    while x<width and x>0 and y<height and y>0:        
        points.append([x,y])        
        x=int(x0+i)
        y=int(y0+k*i)
        i=i+1

    return sorted(points, key=lambda point: point[0])


def gauss(x, B, A, x0, sigma): 
    return B + A*np.exp(-(x - x0)**2/(2*sigma**2))



class ImageLoaderApp(QMainWindow, Ui_Laser):
    def __init__(self):
        super(ImageLoaderApp, self).__init__()
        self.setupUi(self)

        self.image_data = None
        self.sorted_points = None
        self.curve_data = None
        self.x_array=[]
        self.y_array=[]
        # Find the button and graphics view in the UI

        self.scene = QGraphicsScene()
        self.image.setScene(self.scene)
        self.scene2 = QGraphicsScene()
        self.fit.setScene(self.scene2)

        # Connect the button click event to the loadImage method
        self.load.clicked.connect(self.loadImage)
        self.plot.clicked.connect(self.plotcurve)
        self.fit_2.clicked.connect(self.fit_curve)
        self.save.clicked.connect(self.saveToFile)
        self.draw.clicked.connect(self.draw_line)


    def loadImage(self):
        # Open a file dialog to select an image file
        options = QFileDialog.Options()
        self.x_array=[]
        self.y_array=[]
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.bmp);;All Files (*)", options=options)
        if fileName:
            # Load the image and convert to grayscale
            image = QImage(fileName)
            grayscale_image = image.convertToFormat(QImage.Format_Grayscale8)
            self.x_array=[]
            self.y_array=[]
            # Convert QImage to numpy array
            width = grayscale_image.width()
            height = grayscale_image.height()
            ptr = grayscale_image.bits()
            ptr.setsize(height * width)
            grayscale_array = np.array(ptr).reshape((height, width))

            # Store the image data in the instance variable
            self.image_data = grayscale_array
            # Display the brightness values in the QGraphicsView with a color bar and title
            self.displayBrightness(grayscale_array, self.x_array,self.y_array)


    def draw_line(self):
        # Open a file dialog to select an image file
        dat = self.image_data
        plt.figure()
        x_0 = float(self.x0.text())
        y_0 = float(self.y0.text())
        slope = float(self.slope.text())

        print(x_0,y_0,slope,len(dat[0]),len(dat))

        self.sorted_points = get_line_coordinates(x_0, y_0, slope,width=len(dat[0]),height=len(dat))

        self.x_array=[]
        self.y_array=[]

        for i in self.sorted_points:
            self.x_array.append(i[0])
            self.y_array.append(i[1])

        self.displayBrightness(dat, self.x_array,self.y_array)        

        


    def plotcurve(self):

        brightness_data=[]
        dat=self.image_data
        for i in self.sorted_points:
            brightness_data.append(dat[i[1]][i[0]])

        plt.plot(np.linspace(0,len(self.sorted_points)-1,len(self.sorted_points)), brightness_data)
        plt.ylabel("Brightness")
        plt.xlabel("# of points in x axis")

        self.curve_data=[np.linspace(0,len(self.sorted_points)-1,len(self.sorted_points)), brightness_data]
        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a QPixmap from the buffer
        image2 = QPixmap()
        image2.loadFromData(buf.getvalue())
        
        scene = QGraphicsScene()
        scene.addPixmap(image2)
        self.fit.setScene(scene)
        self.fit.fitInView(scene.sceneRect(), mode=1)

    def saveToFile(self):

        dat = self.curve_data
        # Open a file dialog to specify the save location and file name
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if fileName:
            # Save the arrays to a text file as two columns
            try:
                with open(fileName, 'w') as file:
                    for a, b in zip(dat[0], dat[1]):
                        file.write(f"{a}\t{b}\n")
                QMessageBox.information(self, "Success", f"Data saved to {fileName}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")

    def fit_curve(self):
        # Open a file dialog to select an image file
        dat = self.curve_data
        AA=float(self.AA.text())
        BB=float(self.BB.text())
        x00=float(self.x00.text())
        sigma=float(self.sigma.text())

        plt.figure()
        popt, pcov = curve_fit(gauss, dat[0], dat[1], p0 = (BB,AA,x00,sigma))
        plt.plot(dat[0],dat[1])
        plt.plot(dat[0],gauss(dat[0],popt[0],popt[1],popt[2],popt[3]))
        self.BB.setText(str(round(popt[0],3)))
        self.AA.setText(str(round(popt[1],3)))
        self.x00.setText(str(round(popt[2],3)))
        self.sigma.setText(str(abs(round(popt[3],3))))
        # Save the plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Create a QPixmap from the buffer
        image2 = QPixmap()
        image2.loadFromData(buf.getvalue())
        
        scene = QGraphicsScene()
        scene.addPixmap(image2)
        self.fit.setScene(scene)
        self.fit.fitInView(scene.sceneRect(), mode=1)


    def displayBrightness(self, grayscale_array,xx,yy):

        fig = Figure()  # Set the figure size (width, height) in inches
        ax = fig.add_subplot(111)
        # Display the image data with a color bar
        cax = ax.imshow(grayscale_array, cmap='gray', aspect='auto')
        fig.colorbar(cax, ax=ax, label='Brightness')
        # Add the red line to the image
        ax.plot(xx, yy, color='red', linewidth=2)
        # Set the title and axis labels with custom fonts
        title_font = {'fontsize': 18, 'fontweight': 'bold'}
        label_font = {'fontsize': 14}

        ax.set_title('Image Brightness', fontdict=title_font)
        ax.set_xlabel('X Axis pixels', fontdict=label_font)
        ax.set_ylabel('Y Axis pixels', fontdict=label_font)

        # Convert the Matplotlib figure to a QPixmap and display it in the QGraphicsView
        canvas = FigureCanvas(fig)
        canvas.draw()
        width, height = canvas.get_width_height()
        image = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        pixmap = QPixmap(image)

        self.scene.addPixmap(pixmap)
        self.image.fitInView(self.scene.sceneRect(), mode=1)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageLoaderApp()
    window.show()
    sys.exit(app.exec_())
