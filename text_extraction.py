import pytesseract
from pytesseract import Output
import numpy as np
import cv2
import subprocess
import pandas as pd
import ast
from table_detect import table_detect, colfilter
from pdf2image import convert_from_path 

cmd = 'convert annotate/page_1.jpg -type Grayscale -negate -define morphology:compose=darken -morphology Thinning "Rectangle:1x50+0+0<" -negate annotate/4_1.jpg'
subprocess.call(cmd, shell=True)

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def get_text(annotate_dict, tmp_image, w, h):
    tmp3 = tmp_image
    print(tmp3.shape)
    ind = 0
    for ind in range(len(annotate_dict)-1):
        coord = list(annotate_dict['page '+str(ind+1)].values())[:-1]
        for crds in coord:
            x,y,x1,y1 = crds
            x = int((700/w)*x)
            y = int((1000/h)*y)
            x1 = int((700/w)*x1)
            y1 = int((1000/h)*y1)
            sb_img = tmp3[y-2:y1+2, x-2:x1+2]
#            cv2.imshow("TMP_IMG", sb_img)
#            cv2.waitKey()
            d = pytesseract.image_to_data(sb_img, output_type=Output.DICT, lang='eng', config='--psm 6')
            cv2.rectangle(tmp3, (x-1, y-1), (x1+1, y1+1), (0, 0, 255), 2)
            for t in d['text']:
                print(t, end='  ')
            print()
            
    cv2.imshow("Img", tmp3)
    cv2.waitKey()
    cv2.imwrite('output.png', tmp3)
        
        
def get_annotations_xlsx(path):
    df = pd.read_csv(path, header=None)
    annotate_dict = {}
    number_of_rows = df.shape[0]
    for r in range(0,number_of_rows-1):
        row1 = df.iloc[r,:]
        curr_row = row1.tolist()
        #print(curr_row)
        annotate_dict['page '+str(r+1)] = dict()
        for i in range(1,len(curr_row)):
            res = ast.literal_eval(curr_row[i])
            label = res['label']
            x1 = int(res['left'])
            x2 = x1 + int(res['width'])
            y1 = int(res['top'])
            y2 = y1 + int(res['height'])
            annotate_dict['page '+str(r+1)][label] = (x1,y1,x2,y2)
    annotate_dict['ncols'] = df.iloc[number_of_rows-1,1]
    return annotate_dict


large = cv2.imread('annotate/page_1.jpeg')
annotate_dict = get_annotations_xlsx("annotate/inv-7-temp.csv")
print(annotate_dict)
print(large.shape[0],large.shape)
h = large.shape[0]
w = large.shape[1]
rgb = cv2.resize(large, (700, 1000))
cv2.imwrite("current.jpg", rgb)
#kernel = np.array([[0, -1, 0], 
#                   [-1, 5,-1], 
#                   [0, -1, 0]])
#rgb = cv2.filter2D(rgb, -1, kernel)   

#cv2.imshow('rects', rgb)
#cv2.waitKey(0)
#x,y,x1,y1 = (961, 1774, 1932, 2004)
#new_image = large[y:y1,x:x1]
#cv2.imwrite("Cropped.png", new_image)
#cv2.imshow("Img", new_image)
#cv2.waitKey()

new_crd = table_detect(rgb)
NO_OF_COLS = annotate_dict['ncols']           #*************     MENTION NO. OF COLS **********************
start_of_table = int(annotate_dict['page 1']['Start of Table'][1]*1000/h)

new_lst = list()
new_lst2 = list()

for x in new_crd: 
    if colfilter(x,rgb,NO_OF_COLS,start_of_table) == int(NO_OF_COLS):
        new_lst.append(x)
    else :
        new_lst2.append(x)
    
#print(new_lst)
tmp3 = np.copy(rgb)
for crds in new_lst:
    x,y,x1,y1 = crds
    sub_image = tmp3[y-2:y1+2, x-2:x1+2]
    d = pytesseract.image_to_data(sub_image, output_type=Output.DICT, lang='eng', config='--psm 6')
    cv2.rectangle(tmp3, (x-1, y-1), (x1+1, y1+1), (0, 0, 255), 1)
    for t in d['text']:
        print(t, end='  ')
    print()
cv2.imshow("Img", tmp3)
cv2.waitKey()
cv2.imwrite('output.png', tmp3)

get_text(annotate_dict, np.copy(rgb), w, h)
        