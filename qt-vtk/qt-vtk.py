"""
References
http://www.vtk.org/Wiki/VTK/Examples/Python/Widgets/EmbedPyQt2
http://web.mit.edu/16.225/dv/VTK/Wrapping/Python/vtk/qt4/QVTKRenderWindowInteractor.py
http://public.kitware.com/pipermail/vtkusers/2010-November/064086.html
http://www.vtk.org/Wiki/VTK/Examples/Python/Widgets/EmbedPyQt
"""

import sys
import vtk
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.misc import vtkGetDataRoot
import xml.etree.ElementTree as ET
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication, QMessageBox
import matplotlib.pyplot as plt

def get_image_filename():
    #if len(filename) < 1:
        #filename = "image.png"
    filename = "../~image.png"
    return filename

def get_volume_filename():
    filename = str(QtGui.QFileDialog.getOpenFileName(QtGui.QWidget(), 'Select a volume data set', '../data', "UNC MetaImage (*.mhd *.mha);; All Files (*)"))
    if len(filename ) < 1:
        filename = "../data/nucleon.mhd"
    return filename

# Capture the display and place in a tiff
def CaptureImage(renWin):
    w2i = vtk.vtkWindowToImageFilter()
    #writer = vtk.vtkTIFFWriter()
    writer = vtk.vtkPNGWriter()
    w2i.SetInput(renWin)
    w2i.Update()
    writer.SetInputConnection(w2i.GetOutputPort())
    filename = get_image_filename()
    writer.SetFileName(filename)
    renWin.Render()
    writer.Write()

def check_gl_version_supported(renWin):
    extensions = vtk.vtkOpenGLExtensionManager()
    extensions.SetRenderWindow(renWin)
    print "GL_VERSION_1_2", extensions.ExtensionSupported("GL_VERSION_1_2")
    print "GL_VERSION_1_3", extensions.ExtensionSupported("GL_VERSION_1_3")
    print "GL_VERSION_1_4", extensions.ExtensionSupported("GL_VERSION_1_4")
    print "GL_VERSION_1_5", extensions.ExtensionSupported("GL_VERSION_1_5")
    print "GL_VERSION_2_0", extensions.ExtensionSupported("GL_VERSION_2_0")
    print "GL_VERSION_2_1", extensions.ExtensionSupported("GL_VERSION_2_1")
    print "GL_VERSION_3_0", extensions.ExtensionSupported("GL_VERSION_3_0")    

def load_transfer_function():
    filename = str(QtGui.QFileDialog.getOpenFileName(QtGui.QWidget(), 'Select a transfer function', '../transfer_function', "Voreen transfer functions (*.tfi);; All Files (*)"))
    if len(filename ) < 1:
        filename = "../transferfuncs/nucleon.tfi"
        
    tree = ET.parse(filename)
    root = tree.getroot()
    
    TransFuncIntensity = root.find("TransFuncIntensity")
    domain = TransFuncIntensity.find("domain")
    domain_x = domain.get("x")
    domain_y = domain.get("y")
    threshold = TransFuncIntensity.find("threshold")
    threshold_x = threshold.get("x")
    threshold_y = threshold.get("y")
    
    list_intensity = []
    list_split = []
    list_r = []
    list_g = []
    list_b = []
    list_a = []
    
    for key in root.iter('key'):
        colour = key.find("colorL")
        list_intensity.append(key.find("intensity").get("value"))
        list_split.append(key.find("split").get("value"))
        list_r.append(colour.get("r"))
        list_g.append(colour.get("g"))
        list_b.append(colour.get("b"))
        list_a.append(colour.get("a"))

    # Create transfer mapping scalar value to opacity
    opacityTransferFunction = vtk.vtkPiecewiseFunction()
     
    # Create transfer mapping scalar value to color
    colorTransferFunction = vtk.vtkColorTransferFunction()
    
    max_intensity = 255
    for i in range(len(list_intensity)):
        intensity = float(list_intensity[i]) * max_intensity
        r = float(list_r[i]) / max_intensity
        g = float(list_g[i]) / max_intensity
        b = float(list_b[i]) / max_intensity
        a = float(list_a[i]) / max_intensity
        opacityTransferFunction.AddPoint(intensity, a)
        colorTransferFunction.AddRGBPoint(intensity, r, g, b)

    return opacityTransferFunction, colorTransferFunction

def plot_tf(opacityTransferFunction, colorTransferFunction):
    v4 = [0] * 4
    v6 = [0] * 6
    color_list = []
    opacity_list = []
    intensity_list = []
    N = colorTransferFunction.GetSize()
    for i in range(N):
        colorTransferFunction.GetNodeValue(i, v6)
        opacityTransferFunction.GetNodeValue(i, v4)
        intensity_list.append(v4[0])
        opacity_list.append(v4[1])
        color_list.append([v6[1], v6[2], v6[3]])
    
    x = intensity_list
    y = opacity_list
    colors = color_list
    area = [15**2] * N
    plt.title("Transfer Function")
    plt.xlabel("Intensity")
    plt.ylabel("Opacity")
    plt.scatter(x, y, s=area, color=colors, alpha=0.5)
    plt.plot(x, y, '-o', color=[.6,.6,.6])
    plt.show()
    
class MyMainWindow(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        
        # Set up the user interface from Designer.
        self.ui = uic.loadUi("mainwindow.ui") # widget.ui is generated by Qt Creator
        
        self.ui.actionAbout.triggered.connect(lambda: QtGui.QMessageBox.about(self.ui, "Python Qt Example", "This program displays a UI which is loaded from a .ui file generated by Qt Creator."))
        self.ui.actionExit.triggered.connect(lambda: (
            self.ui.close(),
            QApplication.quit())
        )
        
        self.vtkWidget = QVTKRenderWindowInteractor(self.ui.centralWidget)
        self.ui.verticalLayout.addWidget(self.vtkWidget)
        
        self.ren = vtk.vtkRenderer()
        self.renWin = self.vtkWidget.GetRenderWindow()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()   
        
        volume_filename = get_volume_filename()
        opacityTransferFunction, colorTransferFunction = load_transfer_function()
        plot_tf(opacityTransferFunction, colorTransferFunction)
        
        # Create the reader for the data
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(volume_filename)
        
        # The property describes how the data will look
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()
        
        # for vtkGPUVolumeRayCastMapper
        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(reader.GetOutputPort())        

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)        

        self.ren.AddVolume(volume)
        self.ren.SetBackground(1, 1, 1)
        #self.renWin.SetSize(600, 600)
        #self.renWin.Render()
         
        self.iren.Initialize()
        #self.iren.Start()
        
        check_gl_version_supported(self.renWin)

        self.ui.show()
        CaptureImage(self.renWin)        

if __name__ == "__main__":
    print sys.argv[0]
    print __file__
    app = QtGui.QApplication(sys.argv)
    window = MyMainWindow() 
    sys.exit(app.exec_())
