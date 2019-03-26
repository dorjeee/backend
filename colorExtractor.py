from PIL import Image
import cv2
import numpy
import numpy as np

image = Image.open('final.jpg') 


#image.show()

firstbox = image.crop((0,0,20,29)) #cropping the boxes 
secondbox = image.crop((0,84,20,113))
thirdbox = image.crop((0,124,20,151))
forthbox = image.crop((0,160,20,187))
fifthbox = image.crop((0,200,20,226))
sixthbox = image.crop((0,236,20,261))
seventhbox = image.crop((0,272,20,297))
eighthbox = image.crop((0,344,20,368))
ninthbox = image.crop((0,377,20,403))


properties = [firstbox, secondbox, thirdbox, forthbox, fifthbox, sixthbox, seventhbox, eighthbox, ninthbox]
elements = ['hardness', 'chlorine', 'iron','copper','lead','nitrate','nitrite', 'alkalinity', 'pH']
avg_color = {}

for i in range(8): #getting average rgb values
	avg_color_per_row = numpy.average(properties[i], axis=0) 
	avg_color[i] = numpy.average(avg_color_per_row, axis=0)

for i in range(8): 
	print('For',elements[i],': ',np.round(avg_color[i])) #round up values




