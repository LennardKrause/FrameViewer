import os, argparse, glob, re
import numpy as np
import pyqtgraph as pg

# H5ShowCube
# a tool to show tif data without loading all data
#
# 3d: img_view.getImageItem().image.shape
# 2d: img_view.image.shape
#
# What it does:
# initialize as 3d cube
#  - img_view.setImage(np.zeros((inum,5,5)))
# fix color levels and histogram boundaries
#  - img_view.setLevels(0, data.mean()*25)
#  - img_view.setHistogramRange(0, data.mean()*30)
# force emit image change to load one 2d image
#  - img_view.timeLine.sigPositionChanged.emit(img_view.timeLine)
# reset range to full 2d data
#  - img_view.autoRange()
# update only the 2d image data
#  - img_view.getImageItem().setImage(data, autoHistogramRange=False, autoRange=False, autoLevels=False)
# PyQtGraph gets confused so we need to reset the histogram range
#   img_view.getHistogramWidget().setHistogramRange(*img_view.getImageItem().getLevels())

def init_parser():
    parser = argparse.ArgumentParser(description = '')
    parser.add_argument('-p', required=False, dest='_PATH', type=str, default='/Users/au577597/OneDrive - Aarhus universitet/Github/H5Show/tif', help='path to images')
    parser.add_argument('-s', required=False, dest='_ISUM', type=int, default=1,   help='images to sum')
    return parser.parse_args()

class KeyPressWindow(pg.QtWidgets.QMainWindow):
    sigKeyPress = pg.QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, ev):
        self.sigKeyPress.emit(ev)

def keyPressed(k):
    if k.key() == 65:
        if par.isum == False:
            par.isum = True
            print('Summing Mode: On')
        else:
            par.isum = False
            print('Summing Mode: Off')
    else:
        pass

def read_image(fname):
    ext = os.path.splitext(fname)[1]
    if ext in par.fmts:
        return par.fmts[ext](fname)
    else:
        print('Image format not supported!')
        raise SystemExit

def read_Rayonix(fname):
    with open(fname, 'rb') as b:
        # we are not interested in the header
        #head = b.read(4096).decode('unicode_escape')
        b.seek(4096)
        data = np.ndarray(shape=(1920, 1920), dtype=np.int16, buffer=b.read())
    return data

def read_Pilatus3X1M(fname):
    with open(fname, 'rb') as b:
        # we are not interested in the header
        #head = b.read(4096).decode('unicode_escape')
        b.seek(4096)
        data = np.ndarray(shape=(1043, 981), dtype=np.int32, buffer=b.read(4092732))
    return data

def read_sfrm(fname):
    '''
     Read Bruker .sfrm frame
     - header is returned as continuous stream
     - information read from header 
       - detector dimensions (NROWS, NCOLS)
       - bytes per pixel of image (NPIXELB)
       - number of pixels in 16 and 32 bit overflowtables (NOVERFL)
     - data is returned as uint32 2D-Array
    '''
    #def chunkstring(string, length):
    #    '''
    #     return header as list of tuples
    #      - splits once at ':'
    #      - keys and values are stripped strings
    #      - values with more than 1 entry are un-splitted
    #    '''
    #    return list(tuple(map(lambda i: i.strip(), string[0+i:length+i].split(':', 1))) for i in range(0, len(string), length)) 
    #header_list = chunkstring(header, 80)
    with open(fname, 'rb') as f:
        # read the first 512 bytes
        # find keyword 'HDRBLKS' 
        header_0 = f.read(512).decode()
        # header consists of HDRBLKS x 512 byte blocks
        header_blocks = int(re.findall('\s*HDRBLKS\s*:\s*(\d+)', header_0)[0])
        # read the remaining header
        header = header_0 + f.read(header_blocks * 512 - 512).decode()
        # extract frame info:
        # - rows, cols (NROWS, NCOLS)
        # - bytes-per-pixel of image (NPIXELB)
        # - length of 16 and 32 bit overflow tables (NOVERFL)
        nrows = int(re.findall('\s*NROWS\s*:\s*(\d+)', header)[0])
        ncols = int(re.findall('\s*NCOLS\s*:\s*(\d+)', header)[0])
        npixb = int(re.findall('\s*NPIXELB\s*:\s*(\d+)', header)[0])
        nov16, nov32 = list(map(int, re.findall('\s*NOVERFL\s*:\s*-*\d+\s+(\d+)\s+(\d+)', header)[0]))
        # calculate the size of the image
        im_size = nrows * ncols * npixb
        # bytes-per-pixel to datatype
        bpp2dt = [None, np.uint8, np.uint16, None, np.uint32]
        # reshape data, set datatype to np.uint32
        data = np.frombuffer(f.read(im_size), bpp2dt[npixb]).reshape((nrows, ncols)).astype(np.uint32)
        # read the 16 bit overflow table
        # table is padded to a multiple of 16 bytes
        read_16 = int(np.ceil(nov16 * 2 / 16)) * 16
        # read the table, trim the trailing zeros
        table_16 = np.trim_zeros(np.frombuffer(f.read(read_16), np.uint16))
        # read the 32 bit overflow table
        # table is padded to a multiple of 16 bytes
        read_32 = int(np.ceil(nov32 * 4 / 16)) * 16
        # read the table, trim the trailing zeros
        table_32 = np.trim_zeros(np.frombuffer(f.read(read_32), np.uint32))
        # assign values from 16 bit overflow table
        data[data == 255] = table_16
        # assign values from 32 bit overflow table
        data[data == 65535] = table_32
        return data #header, data

def change_image(draw=True):
    # where are we in time?
    _idx = int(round(img_view.timeLine.value(), 0))

    if draw:
        # sum requested number of images
        #_dat = np.zeros(par.dshp)
        #for _i in range(par.xsum):
        #    _dat += read_image(par.imgs[_idx*par.xsum+_i])
        _dat = read_image(par.imgs[_idx])
    
        # fetch the image item
        _img = img_view.getImageItem()
        # update the 2d image data
        if par.isum:
            _img.setImage(par.temp+_dat, autoHistogramRange=False, autoRange=False, autoLevels=False)
            
            par.valthresh = max(np.median(_img.image), 1)*15
            img_view.setLevels(-1, par.valthresh)
            img_view.setHistogramRange(-1, par.valthresh)
        else:
            _img.setImage(_dat, autoHistogramRange=False, autoRange=False, autoLevels=False)
        par.temp = _img.image
        # force reset the histogram range
        img_view.getHistogramWidget().setHistogramRange(*_img.getLevels())
        # get the value from the *2d image* (not img_view.image[x,y])
        _val = _img.image[par._y,par._x]
        # update the label
        label.setText(f'{_idx+1:> 4}/{par.nimg} {par._x:>4}x{par._y:<4}: {_val:.0f}')
    
    # spots
    if par.flag_plot_vals:
        _lmax = img_view.getLevels()[1]
        # calculate pixel values
        if not par.has_scat_for_img == _idx or not par.has_scat_for_lut == _lmax:
            _thresh = max(par.valthresh, _lmax)
            # fetch the image item
            _img = img_view.getImageItem()
            # which pixels to mark
            _pos = np.argwhere(_img.image >= _thresh)
            _spots = [{'pos': i[::-1]+0.5, 'symbol': createLabel(f'{_img.image[i[0], i[1]]:.0f}')} for i in _pos]
            scatter.clear()
            scatter.addPoints(_spots)
            par.has_scat_for_img = _idx
            par.has_scat_for_lut = _lmax
        plot_spots()

def plot_spots():
    if img_view.getView().viewPixelSize()[0] <= par.show_at:
        scatter.show()
        if not par.flag_plot_vals or not par.has_scat_for_lut == img_view.getLevels()[1]:
            par.flag_plot_vals = True
            change_image(draw=False)
    else:
        scatter.hide()
        par.flag_plot_vals = False

def imageHoverEvent(point):
    # get the index
    _idx = int(round(img_view.timeLine.value(),0))
    # map it
    p = img_view.getView().mapSceneToView(point)
    par._x = int(np.clip(p.x(), 0, img_view.getImageItem().image.shape[1] - 1))
    par._y = int(np.clip(p.y(), 0, img_view.getImageItem().image.shape[0] - 1))
    # get the value from the *2d image* (not img_view.image[x,y])
    v = img_view.getImageItem().image[par._y,par._x]
    # update the label
    label.setText(f'{_idx+1:> 4}/{par.nimg} {par._x:>4}x{par._y:<4}: {v:.0f}')

def createLabel(label):
    # QPainterPath
    symbol = pg.QtGui.QPainterPath()
    # creating QFont object
    f = pg.QtGui.QFont()
    # setting font size
    f.setPointSize(10)
    # adding text
    symbol.addText(0, 0, f, label)
    # getting bounding rectangle
    br = symbol.boundingRect()
    # getting scale
    scale = min(0.05, 1. / br.width(), 1. / br.height())
    # getting transform object
    tr = pg.QtGui.QTransform()
    # setting scale to transform object
    tr.scale(scale, scale)
    # translating
    tr.translate(-br.x() - br.width() / 2., -br.y() - br.height() / 2.)
    # returning text symbol
    return tr.map(symbol)

def main():
    # set globals
    # imageHoverEvent and change_image need:
    #  - to access ImageView (img_view)
    #  - to access TextItem (label)
    #  - to access h5 file (h5file)
    #  - to get the h5 name (iname)
    global img_view, scatter, label, par

    pg.setConfigOptions(imageAxisOrder='row-major', background='k', leftButtonPan=True)
    app = pg.mkQApp()

    #_ARGS = init_parser()
    img_path = pg.FileDialog.getOpenFileName(None, 'Open file', '/Users/au577597/Library/CloudStorage/OneDrive-Aarhusuniversitet/Github/FrameWatcher/sfrm/', "Image files (*.img *.sfrm *.tif)")[0]
    #img_path = pg.FileDialog.getOpenFileName(None, 'Open file', "Image files (*.tif *.sfrm)")[0]
    #img_path = '/Users/au577597/Library/CloudStorage/OneDrive-Aarhusuniversitet/Github/FrameWatcher/sfrm/Rubrene_21_data_00_0001.sfrm'

    par = container()
    par.path, par.name = os.path.split(img_path)
    par.fext = os.path.splitext(par.name)[1]
    par.imgs = sorted(glob.glob(os.path.join(par.path, f'*{par.fext}')))
    par.nimg = len(par.imgs)
    par.fmts = {'.sfrm':read_sfrm,
                 '.tif':read_Pilatus3X1M,
                 '.img':read_Rayonix}
    par.temp = read_image(img_path)
    par.dshp = par.temp.shape
    par.isum = False
    par.flag_plot_vals = False
    par.has_scat_for_img = -1
    par.has_scat_for_lut = -1
    par.show_at = 0.1
    par._x = 0
    par._y = 0


    # define grid layout
    layout = pg.QtWidgets.QGridLayout()
    
    # make a widget, set the layout
    centralwidget = pg.QtWidgets.QWidget()
    centralwidget.setLayout(layout)
    
    # build a window, put the widget
    win = KeyPressWindow()#pg.QtWidgets.QMainWindow()
    win.resize(1024,1024)
    win.setWindowTitle(par.name)
    win.setCentralWidget(centralwidget)
    
    # init ImageView
    img_view = pg.ImageView(discreteTimeLine=True)
    layout.addWidget(img_view, 0, 0)

    # set colormap
    img_view.setPredefinedGradient('inferno')

    # hide ui buttons
    img_view.ui.roiBtn.hide()
    img_view.ui.menuBtn.hide()
    
    # add a label to show name, index, x, y and value
    label = pg.TextItem(par.name)
    font = pg.QtGui.QFont('Helvetica', 14, weight=100)
    label.setFont(font)
    img_view.scene.addItem(label)

    # 
    #for _i in range(par.xsum):
    #    first += read_image(par.imgs[_i])
    #    last  += read_image(par.imgs[par.nsum-1-_i])
    par.valthresh = max(np.median(par.temp), 1)*15

    # initialize ImageView with empty 3d cube
    # first dimension must be the number of images
    dummy = np.zeros((par.nimg,par.dshp[0],par.dshp[1]))
    dummy[0,:,:] = read_image(par.imgs[0])
    dummy[-1,:,:] = read_image(par.imgs[-1])
    img_view.setImage(dummy)
    
    # set color levels and histogram ranges to keep them steady
    img_view.setLevels(-1, par.valthresh)
    img_view.setHistogramRange(-1, par.valthresh)

    # plotting the scatter plot
    pen = pg.mkPen(color=(0, 0, 0, 255), width=1)
    brush = pg.mkBrush(color=(0, 0, 0, 255))
    scatter = pg.ScatterPlotItem(pen=pen, brush=brush, size=0.8, useCache=True, pxMode=False)
    
    # adding scatter plot to the plot window
    img_view.getView().addItem(scatter)

    # connect to custom signals
    img_view.scene.sigMouseMoved.connect(imageHoverEvent)
    img_view.timeLine.sigPositionChanged.connect(change_image)
    img_view.getView().sigRangeChangedManually.connect(plot_spots)
    img_view.getHistogramWidget().sigLevelChangeFinished.connect(plot_spots)

    # update the image -> insert 2d image
    change_image(draw=True)

    # call auto range on 2d image to get the correct bounds
    img_view.autoRange()

    win.sigKeyPress.connect(keyPressed)

    win.show()
    pg.mkQApp().exec()

class container(object):
    pass

if __name__ == '__main__':
    main()
