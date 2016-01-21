#!/usr/bin/python

import cairosvg
from PIL import Image
import argparse
import os
import math
import numpy

parser = argparse.ArgumentParser(description='Convert KiCAD Exported SVG files to PNG for milling using FabModules')
parser.add_argument('files', metavar='file.svg', type=open, nargs='+',
                   help='SVG files for conversion')

parser.add_argument('--dpi', metavar='N', type=int,
                   help='DPI for output PNG files (Default 1000 dpi)', default=1000)

parser.add_argument('--padding', metavar='mm', type=int,
                   help='External border padding (Default 2mm)', default=2)

args = parser.parse_args()

paddingpx = math.ceil(( args.padding * 0.0393701 ) * args.dpi)
print("For " + str(args.padding) + "mm of padding at " + str(args.dpi) + " we will add margins of " + str(paddingpx) + " pixels")
for f in args.files:
	outputFile = os.path.splitext(f.name)[0]+".png"
	cairosvg.svg2png( file_obj=f, write_to=outputFile, dpi=args.dpi)

	png = Image.open(outputFile)
	png = png.convert("RGBA")

	pngdata = png.getdata()
	corrected = []

	iscopperlayer = outputFile.find("F.Cu")
	iscutoutlayer = outputFile.find("Edge.Cuts")
	if iscopperlayer > 0:
		print(outputFile+" is a copper layer")
	elif iscutoutlayer > 0:
		print(outputFile+" is a cutout layer")

	# Replace any transparent pixels with white pixels and invert any copper layer images
	for pixel in pngdata:
		if pixel[3] == 0:
			if iscopperlayer>0:
				corrected.append((0,0,0,255))
			else:
				corrected.append((255,255,255,255))
		else:
			if iscopperlayer>0:
				corrected.append((255,255,255,255))
			else:
				corrected.append((0,0,0,255))


	png.putdata(corrected)
	png = png.convert("1")
	oldsize = png.size
	newsize = (int(oldsize[0] + (2*paddingpx)),int(oldsize[1] + (2*paddingpx)))

	## REDO THIS WITH EVEN/ODD FILL RULES!!!
	# Now we nee to flood fill the outside of the cutout with black
	if iscutoutlayer > 0:
		columns = oldsize[0]
		rows = oldsize[1]
		for col in xrange(0,columns):
			if png.getpixel((col,0)) == 255:
				for row in xrange(0,rows):
					if png.getpixel((col,row)) == 255:
						png.putpixel((col,row),0)
					elif png.getpixel((col,row)) == 0:
						break
				for row in xrange(rows,0):
					if png.getpixel((col,row)) == 255:
						png.putpixel((col,row),0)
					elif png.getpixel((col,row)) == 0:
						break

		for row in xrange(0,rows):
			if png.getpixel((row,0)) == 255:
				for col in xrange(0,columns):
					if png.getpixel((col,row)) == 255:
						png.putpixel((col,row),0)
					elif png.getpixel((col,row)) == 0:
						break
				for col in xrange(rows,0):
					if png.getpixel((col,row)) == 255:
						png.putpixel((col,row),0)
					elif png.getpixel((col,row)) == 0:
						break


	finalpng = Image.new("1", newsize)
	finalpng.paste(png, ((newsize[0]-oldsize[0])/2, (newsize[1]-oldsize[1])/2))
	
	png = finalpng
	png.save(outputFile, "PNG")