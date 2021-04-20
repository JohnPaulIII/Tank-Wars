import skimage
from skimage import io, transform
import PIL
from PIL import Image
import numpy as np
import cv2
import imutils
import os

def testskimage():
    rotation = 90
    #filename_in = r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue000.jpg'
    #filename_out = r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue{}.jpg'.format(str(int(rotation)))
    image = skimage.io.imread(r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue000.jpg')
    image1 = skimage.transform.rotate(image, rotation, resize=True, order = 5)
    skimage.io.imsave(r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue{}.jpg'.format(str(int(rotation))), image1)

def testPIL():
    rotation = 45
    im = Image.open(r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue000.jpg')
    im.rotate(rotation).show()
    im1 = im.rotate(rotation)
    im1.save(r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue{}.jpg'.format(str(int(rotation))))

def testPIL2():
    rotation = 90
    filename_in = r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue000.jpg'
    filename_out = r'S:\Users\jcpic\Documents\GitHub\Tank_Base_Blue{}.bmp'.format(str(int(rotation)))
    # original image
    img = Image.open(filename_in)
    # converted to have an alpha layer
    im2 = img.convert('RGBA')
    # rotated image
    rot = im2.rotate(rotation, resample=Image.BICUBIC)
    # a white image same size as rotated image
    fff = Image.new('RGBA', rot.size, (255,)*4)
    # create a composite image using the alpha layer of rot as a mask
    out = Image.composite(rot, fff, rot)
    # save your work (converting back to mode='1' or whatever..)
    out.convert(img.mode).save(filename_out)

def testcv2():
    rotation = 45
    filename_in = r'S:\Users\jcpic\Documents\GitHub\testAssets\Tank_Base_Blue000.jpg'
    filename_out = r'S:\Users\jcpic\Documents\GitHub\testAssets\Tank_Base_Blue{}.bmp'.format(str(int(rotation)))
    img1 = cv2.imread(filename_in)
    rotated = imutils.rotate(img1, rotation)
    print(rotation)
    cv2.imshow("Rotated", rotated)
    cv2.waitKey(0)

def rotatedPIL(image, rotation):
    im2 = image.convert('RGBA')
    rot = im2.rotate(rotation, resample=Image.BICUBIC)
    fff = Image.new('RGBA', rot.size, (255,)*4)
    return Image.composite(rot, fff, rot)

def createSpritesheet(colors):
    stepangle = 6
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    for color in colors:
        color = color[2]
        baseimage = Image.open(os.path.join(curr_dir, 'Tank_Base_{}000.bmp'.format(color)))
        baseimage = baseimage.convert('RGBA')
        turrentimage = Image.open(os.path.join(curr_dir, 'Tank_Turrent_{}000.bmp'.format(color)))
        turrentimage = turrentimage.convert('RGBA')
        n, m = baseimage.size
        masterwidth = int(n * 180 / stepangle)
        masterheight = m * 4
        image = Image.new(baseimage.mode, (masterwidth, masterheight))
        for i in range(360, 0, -stepangle):
            if i == 360:
                newbase = baseimage
                newturrent = turrentimage
            else:
                newbase = rotatedPIL(baseimage, i)
                newturrent = rotatedPIL(turrentimage, i)
            if i > 180:
                image.paste(newbase, (int((360 - i) * n / stepangle), 0))
                image.paste(newturrent, (int((360 - i) * n / stepangle), m))
            else:
                image.paste(newbase, (int((180 - i) * n / stepangle), 2 * m))
                image.paste(newturrent, (int((180 - i) * n / stepangle), 3 * m))
        image.save(os.path.join(curr_dir, '{}_Tank_Sprites.bmp'.format(color)))

def createBaseImages(colors):
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    baseimage = Image.open(os.path.join(curr_dir, 'Tank_Base_Green000.bmp'))
    baseimage = baseimage.convert('RGBA')
    turrentimage = Image.open(os.path.join(curr_dir, 'Tank_Turrent_Green000.bmp'))
    turrentimage = turrentimage.convert('RGBA')
    for color in colors:
        data = np.array(baseimage)
        red, green, blue, alpha = data.T
        white_areas_light = (red == 17) & (blue == 45) & (green == 127)
        white_areas_dark = (red == 10) & (blue == 46) & (green == 77)
        data[..., :-1][white_areas_light.T] = color[0]
        data[..., :-1][white_areas_dark.T] = color[1]
        newimage = Image.fromarray(data)
        newimage.save(os.path.join(curr_dir, 'Tank_Base_{}000.bmp'.format(color[2])))
        data = np.array(turrentimage)
        red, green, blue, alpha = data.T
        white_areas_light = (red == 17) & (blue == 45) & (green == 127)
        white_areas_dark = (red == 10) & (blue == 46) & (green == 77)
        data[..., :-1][white_areas_light.T] = color[0]
        data[..., :-1][white_areas_dark.T] = color[1]
        newimage = Image.fromarray(data)
        newimage.save(os.path.join(curr_dir, 'Tank_Turrent_{}000.bmp'.format(color[2])))
        #turrentdata = np.array(turrentimage)

def imageMask():
    filename_in = r'S:\Users\jcpic\Documents\GitHub\Tank-Wars\testAssets\Black_Tank_Sprites.bmp'
    thresholdnum = 254
    img2 = cv2.imread(filename_in)
    cv2.imshow('Original', img2)
    cv2.waitKey(0)
    img2gray = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)
    mask = cv2.threshold(img2gray, thresholdnum, 255, cv2.THRESH_BINARY)[1]
    mask_inv = cv2.bitwise_not(mask)
    kernel5 = np.ones((5,5),np.uint8)
    kernel9 = np.ones((9,9),np.uint8)
    erosion = cv2.erode(mask_inv,kernel5,iterations = 2)
    cv2.imshow('Processed', erosion)
    cv2.waitKey(0)

if __name__ == "__main__":
    '''
    colors = [
        ((197, 17, 17), (122, 8, 56), 'Red'),
        ((19, 46, 209), (9, 21, 142), 'Blue'),
        ((237, 84, 186), (171, 43, 173), 'Pink'),
        ((239, 125, 13), (179, 62, 21), 'Orange'),
        ((245, 245, 87), (194, 135, 34), 'Yellow'),
        ((63, 71, 78), (30, 31, 38), 'Black'),
        ((214, 224, 240), (131, 148, 191), 'White'),
        ((107, 47, 187), (59, 23, 124), 'Purple'),
        ((113, 73, 30), (94, 38, 21), 'Brown'),
        ((56, 254, 220), (36, 168, 190), 'Cyan'),
        ((80, 239, 57), (21, 167, 66), 'Lime'),
    ]
    createBaseImages(colors)
    createSpritesheet(colors)
    '''
    imageMask()
#testcv2()