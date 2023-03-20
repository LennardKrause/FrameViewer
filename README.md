# FrameViewer
Simple python frame viewer

### Currently understands:
 - .tif (Dectris Pilatus3)
 - .sfrm (Bruker)

### Uses numpy to do the math, pyqtgraph do display the image and python to hold it all together.

### WIP feature list:
 - Zoom in (enough) shows the intensities for all pixel above the current threshold (slider)
 - the 'a' button toggles summation mode (changing image doesn't clear canvas)
 
### WIP bug list:
 - histogram bugged when changing to first/last image (because of hacky slider implementation, tbf!)
