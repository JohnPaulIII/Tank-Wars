import skimage
from skimage import io, transform
import PIL
from PIL import Image

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

testPIL2()