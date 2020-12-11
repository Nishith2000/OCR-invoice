import pandas as pd
from table_detect import table_detect, colfilter
import ast

def get_annotations_xlsx(path):
    df = pd.read_csv(path, header=None)
    annotate_dict = {}
    number_of_rows = df.shape[0]
    for r in range(0,number_of_rows-1):
        row1 = df.iloc[r,:]
        curr_row = row1.tolist()
        print(curr_row)
        annotate_dict['page '+str(r+1)] = []
        for i in range(1,len(curr_row)):
            res = ast.literal_eval(curr_row[i])
            label = res['label']
            x1 = int(res['left'])
            x2 = x1 + int(res['width'])
            y1 = int(res['top'])
            y2 = y1 + int(res['height'])
            annotate_dict['page '+str(r+1)].append(
                        {
                            label:(x1,y1,x2,y2)
                        }
                    )
    annotate_dict['ncols'] = df.iloc[number_of_rows-1,1]
    return annotate_dict

temp = get_annotations_xlsx("annotate/def.csv")
print(temp)