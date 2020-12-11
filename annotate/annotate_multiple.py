import base64
import datetime
import dash
import json
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_canvas
import dash_table
import pandas as pd
from dash_canvas.utils import parse_jsonstring_rectangle
from dash_canvas.components import image_upload_zone
from PIL import Image
from io import BytesIO
import base64
import csv
from numpy import asarray
from pdf2image import convert_from_path,convert_from_bytes

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

list_columns = ['width', 'height', 'left', 'top', 'label']
columns = [{'name': i, "id": i} for i in list_columns]
columns[-1]['presentation'] = 'dropdown'
list_preferred = ['Company Name','Company Address','Invoice Number','Start of Table','End of Table','Subtotal','Tax','Total']
shortlists = [{'label': i, 'value': i} for i in list_preferred]

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=[
            'Drag and Drop or ',
            html.A('Select a PDF')],
        style={'width': str(100) + '%',
               'height': '50px',
               'lineHeight': '50px',
               'borderWidth': '1px',
               'borderStyle': 'dashed',
               'borderRadius': '5px',
               'textAlign': 'center'
               },
        multiple=False,
    ),
    html.Div(id='view-output'),
    html.Button('Previous', id='getprev', n_clicks=0),
    html.Button('Next', id='getnext', n_clicks=0),
    dash_canvas.DashCanvas(
                            id='canvas',
                            tool='rectangle',
                            lineWidth=2,
                            lineColor='rgba(255,0, 0, 0.5)',
                            hide_buttons=['pencil', 'line'],
                            goButtonTitle='Label'
                            ),
    html.Div([
        html.Div([
                html.H3('Label images with bounding boxes'),
                ]),
        html.Div([
                dash_table.DataTable(
                                    id='table',
                                    columns=columns,
                                    editable=True,
                                    dropdown = {'label': {'options': shortlists}},
                                    ),
                ])
    ]),
    dcc.Input(
            id="input_columns",
            type="number",
            placeholder="Number of columns",
        ),
    dcc.Input(
            id="input_filename",
            type="text",
            placeholder="File name",
        ),
    html.Button('Done', id='done', n_clicks=0),
    html.Div(id = 'done-output'),
])

#---helpers---

page_count = 0
prev = None
pdfpages = []
pagecsv = {}
tabresultsperpage = []

def checkprev(imgsrc):
    global prev
    if prev==imgsrc or prev==None:
        return True
    else:
        return False

def update_prev(imgsrc):
    global prev
    prev = imgsrc
    return prev

def image_to_data_url(filename, dtype=None):
    ext = filename.split('.')[-1]
    prefix = f'data:image/{ext};base64,'
    with open(filename, 'rb') as f:
        img = f.read()
    image_string = prefix + base64.b64encode(img).decode('utf-8')
    return image_string

def extractpages(uploaded_file_contents,uploaded_file_name):
    global pdfpages
    global tabresultsperpage
    # Parse base64 encoded pdf and save in system
    x = uploaded_file_contents.split(',')[1:2]
    base64string = x[0]
    '''
    with open(uploaded_file_name, 'wb') as theFile:
        theFile.write(base64.b64decode(base64string))       #only if you want to save pdf 
    pages = convert_from_path(uploaded_file_name, 200)
    '''
    base64_bytes = base64string.encode("ascii")
    message_bytes = base64.b64decode(base64_bytes)
    pages = convert_from_bytes(message_bytes, 200, use_pdftocairo=True,fmt="jpeg")
    image_counter = 1
    for page in pages:
        # Save the image of the page in system
        filename = "page_"+str(image_counter)+".jpeg"
        page.save(filename, 'JPEG')
        pdfpages.append(image_to_data_url(filename))
        tabresultsperpage.append(None)
        image_counter = image_counter + 1

#---callbacks---
invoice_name = None

@app.callback(Output('done-output','children'),[Input('done','n_clicks')],[State('table','data'),State('input_columns','value'),State('input_filename','value')],prevent_initial_call=True)
def updateout(_,tab_data,no_of_columns,filename):
    global pagecsv
    global pdfpages
    global page_count
    if len(pdfpages)!=0 and no_of_columns!=None:
        if filename==None or filename=='':
            filename = invoice_name
        no_of_columns = int(no_of_columns)
        pg = 'Page '+str(page_count+1)
        if tab_data!=None:
            pagecsv[pg] = tab_data
        pagecsv['No of Columns'] = [no_of_columns]
        pagecsv = dict(filter(lambda ele:ele[1]!=None,pagecsv.items())) # remove all instances where a page has not been annotated
        pd.DataFrame.from_dict(data=pagecsv, orient='index').to_csv(filename+'.csv', header=False)
        return html.H3('Annotation results saved as {}'.format(filename))
    elif len(pdfpages) == 0:
        return html.H3('Load a document to annotate and save results')
    elif no_of_columns==None:
        return html.H3('Enter number of columns in table')

@app.callback([Output('canvas', 'image_content'),Output('view-output','children')], [Input('upload-data', 'contents'), Input('getprev', 'n_clicks'), Input('getnext', 'n_clicks')], [State('upload-data', 'filename'), State('upload-data', 'last_modified'), State('table', 'data')], prevent_initial_call=True)
def update_canvas_upload(image_string,a,b,image_name,image_lm,tab_data):
    global pdfpages
    global page_count
    global pagecsv
    global tabresultsperpage
    global invoice_name
    invoice_name = image_name.split('.')[0]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'getprev' in changed_id:
        if page_count>0:
            pg = 'Page '+str(page_count+1)
            pagecsv[pg] = tab_data
            tabresultsperpage[page_count]=tab_data
            page_count-=1
            return pdfpages[page_count],html.H5('Viewing page %d'%(page_count+1))
        return pdfpages[page_count],html.H5('No page before First page')
        
    elif 'getnext' in changed_id:
        if page_count <len(pdfpages)-1:
            pg = 'Page '+str(page_count+1)
            pagecsv[pg] = tab_data
            tabresultsperpage[page_count] = tab_data
            page_count += 1
            return pdfpages[page_count], html.H5('Viewing page %d' % (page_count+1))
        return pdfpages[page_count],html.H5('No page after Last page')
    else:    
        if image_string is None:
            raise ValueError
        if image_string is not None:
            page_count = 0
            pdfpages = []
            pagecsv = {}
            tabresultsperpage = []
            extractpages(image_string,image_name)
            return pdfpages[page_count], html.H5('Viewing page %d' % (page_count+1))
        return None,None

'''
separate [Input('canvas', 'json_data'),Input('canvas', 'image_content')] into 2 different functions
'''

@app.callback(Output('table', 'data'), [Input('canvas', 'json_data'),Input('canvas', 'image_content')], [State('table','data')],prevent_initial_call=True)
def show_string(json_data,img_content,table_data):
    global page_count
    global pagecsv
    global tabresultsperpage
    if checkprev(img_content):
        update_prev(img_content)
        j = json.loads(json_data)
        if len(j["objects"])>0:
            box_coordinates = parse_jsonstring_rectangle(json_data)
            if len(box_coordinates)>0:
                df = pd.DataFrame(box_coordinates, columns=list_columns[:-1])
                stdt = df.to_dict('records')
                if table_data!=None:
                    if tabresultsperpage[page_count]==None:
                        for i in range(len(table_data)):
                            stdt[i]['label'] = table_data[i]['label']
                    else:
                        x = tabresultsperpage[page_count][:]
                        x.extend(stdt)
                        for i in range(len(table_data)):
                            x[i]['label'] = table_data[i]['label']  
                        stdt = x             
                pg = 'Page '+str(page_count+1)
                pagecsv[pg] = stdt
                return stdt
        raise dash.exceptions.PreventUpdate
    else:
        update_prev(img_content)
        if tabresultsperpage[page_count] != None:
            return tabresultsperpage[page_count]
        else:
            return None

if __name__ == '__main__':
    app.run_server(debug=True)
