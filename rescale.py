import os
import sys
from PIL import Image

RARE_COLOR = [0, 255, 0]
THRESHOLD = 0.25

def convert_to_bmp(infile):
	if ".png" in infile:
		f, e = os.path.splitext(infile)

		outfile = f + ".bmp"

		if infile != outfile:
			try:
				with Image.open(infile) as img:
					img = img.quantize(colors=256)
					img = img.convert(mode='P')

					palette = img.getpalette()
					color_counts = sorted(img.getcolors(), reverse=True)
					palette_index = color_counts[0][1]
					palette_use = color_counts[0][0]

					percentage = palette_use / (img.size[0] * img.size[1])

					should_mask = len(color_counts) == 256 or palette_index == 0
					
					# if you dont want to maask texture then add another arugment to the script
					do_mask = sys.argv[2] == None

					if do_mask and should_mask and percentage > THRESHOLD and (len(palette) // 3 == 256):

						print(infile)

						for x in range(img.size[0]):
							for y in range(img.size[1]):
								curr = (x, y)
								if img.getpixel(curr) == palette_index:
									img.putpixel(curr, 255)
								elif img.getpixel(curr) == 255:
									img.putpixel(curr, palette_index)

						# by default alpha is black, let's make it GREEN
						palette[255*3+0] = RARE_COLOR[0]
						palette[255*3+1] = RARE_COLOR[1]
						palette[255*3+2] = RARE_COLOR[2]

						img.putpalette(palette)

					img.save(outfile)
			except OSError:
				print("cannot convert", infile)

def recursive_convert(ent):
	if os.path.isfile(ent):
		convert_to_bmp(ent)
		return

	for folders in os.listdir(ent):
		path = os.path.realpath(os.path.join(ent, folders))
		recursive_convert(path)


def main():
	if sys.argv[1] == None:
		sys.exit(1)

	# if you dont want to maask texture then add another arugment to the script

	path = os.path.realpath(sys.argv[1])
	recursive_convert(path)

if __name__ == "__main__":
	main()