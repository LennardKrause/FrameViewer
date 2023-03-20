# FrameViewer
Simple python frame viewer

### It currently understands:
 - .tif (Dectris Pilatus3)
 - .sfrm (Bruker)

### Uses numpy to do the math and pyqtgraph do display the image.

### WIP feature list:
 - Zoom in (enough) shows the intensities for all pixel above the current threshold (slider)
 - the 'a' button toggles summation mode (don't clear canvas after image change, add instead)
 
### WIP bug list:
 - histogram bugged when changing to first/last image (because of hacky slider implementation, tbf!)
