import os
import sys
from PIL import Image
import math

# RARE_COLOR = [0, 255, 0]
BLEND_THRESHOLD = 0.5

def array_scalar(arr, scalar):
	return [i * scalar for i in arr]

def array_addition(arr1, arr2):
	assert len(arr1) == len(arr2)

	return [arr1[i] + arr2[i] for i in range(len(arr1))]

def array_round(arr):
	return [round(i) for i in arr]

def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 

def blend_texture(img1_path, img2_path, blend_img_path):
	img1 = Image.open(img1_path)
	img2 = Image.open(img2_path)
	blend_img = Image.open(blend_img_path)

	assert img1.size == img2.size, "Images don't have matching dimensions"
	assert img2.size == blend_img.size, "Images don't have matching dimensions"

	# assume uniform modulation for now
	modulation_val = blend_img.getpixel((0, 0))[0]
	modulation_count = 256 // (modulation_val + 1)

	for i in range(modulation_count):
		result = Image.new("RGB", img1.size)
		f, e = os.path.splitext(img1_path)
		result_file = f"{f}_blend{i}.bmp"
		print(f"Processing: {result_file}")

		for x in range(img1.size[0]):
			for y in range(img1.size[1]):
				curr = (x, y)

				blend_pixel = blend_img.getpixel(curr)

				modulation_strength = math.sin((x + (i + 1)*modulation_val) / (modulation_val * modulation_count))

				mask_value = (blend_pixel[1] / 256) * (modulation_strength)

				if mask_value < BLEND_THRESHOLD:
					u = array_scalar(img1.getpixel(curr), mask_value)
					v = array_scalar(img2.getpixel(curr), 1 - mask_value)
					color = array_addition(u,v)
					color = array_round(color)

					result.putpixel(curr, tuple(color))
				else:
					result.putpixel(curr, img1.getpixel(curr))

		result.save(result_file)
		# sys.exit()


def main():
	if len(sys.argv) != 4:
		sys.exit(1)

	img1 = os.path.realpath(sys.argv[1])
	img2 = os.path.realpath(sys.argv[2])
	blend_img = os.path.realpath(sys.argv[3])
	
	blend_texture(img1, img2, blend_img)

if __name__ == "__main__":
	main()