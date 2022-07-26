import streamlit as st
import os
import pandas as pd
import numpy as np
import pdfplumber
from PIL import Image
from stqdm import stqdm
from util import *
from caption_extraction import *
import zipfile

st.title('DART-based 기업공시 Object Extractor')


#########

uploaded_files = st.file_uploader('Drop your pdf', type='pdf',        accept_multiple_files=True)
download_togle = False

process_button = st.button('process pdf')

# display document

options = st.sidebar.multiselect(
    'select object',
    ['Image', 'Table'])

number = st.sidebar.slider('caption parameter', 0, 100, 50)

if uploaded_files is not None and process_button:

    st.header('File Processing')
    my_bar = st.progress(0)
    for i_th_file, uploaded_file in enumerate(uploaded_files):

        with open(os.path.join('pdf_file', uploaded_file.name), 'wb') as f:
            f.write(uploaded_file.getbuffer())
        f.close()

        uploaded_file_name = uploaded_file.name
        # with pdfplumber.open(uploaded_file_name) as pdf:
        #     pages = pdf.pages
        pdf = pdfplumber.open(os.path.join('pdf_file', uploaded_file_name))
        pages = pdf.pages

        # 저장용 pdf 별 object dictionary 생성
        text_dict = {}
        image_dict = {}
        table_dict = {}
        
        # 이미지 모음
        img_list = []
        
        
        # 각 page 루프
        for i, page in stqdm(enumerate(pages)):

            # text, image 객체 추출
            text = get_text(page)
            image = get_image(page)
            # tableobject 객체 딕셔너리로 변환
            table_obj = get_table(page)
            table = []
            for tboj in table_obj:
                table.append(table_object_to_dict(tboj))

            # page 별로 저장
            text_dict[i] = text
            image_dict[i] = image
            table_dict[i] = table
            # st.header('This is table summary')
            # st.caption(table)

            
            im = page.to_image(resolution=400)

            if table and 'Table' in options:
                table_bbox_list = [i.bbox for i in table_obj]
                print(i, 'page Table', table_bbox_list)
                for bbox in bbox_padding(table_bbox_list):
                    im.draw_rect(bbox, stroke='red')



            if image and 'Image' in options:
                page_height = page.height

                img_bbox_list = [(image['x0'], page_height - image['y1'], image['x1'], page_height - image['y0']) for image in image]
                print(i, 'page Image', img_bbox_list)
                for bbox in bbox_padding(img_bbox_list):
                    im.draw_rect(bbox, stroke='blue')
            
            img_list.append(im)

        if not os.path.exists(os.path.join('img_file', uploaded_file_name[:-4])):
            os.makedirs(os.path.join('img_file', uploaded_file_name[:-4]))

        for i, im in enumerate(img_list):
            im.save(os.path.join('img_file', uploaded_file_name[:-4], f'{uploaded_file_name}_{i}.png'), format='PNG')
        
        # progress bar by all file
        my_bar.progress((i_th_file+1)/len(uploaded_files))
        
if uploaded_files and process_button:
    download_togle = True

if download_togle:

    # make zip object
    img_zip = zipfile.ZipFile(os.path.join('output_pdf_file', "processed_file.zip"), 'w')
    print(uploaded_files)
    
    for uploaded_file in uploaded_files:
        
        uploaded_file_name = uploaded_file.name

        img_file_paths = get_file_paths(folder_path=f'img_file/{uploaded_file_name[:-4]}')
        converted_imgs = []
        for path in img_file_paths:
            img_zip.write(path)
    img_zip.close()

    # download button
    with open(os.path.join('output_pdf_file', 'processed_file.zip'), 'rb') as output_zip:
        st.download_button(label="Export_Report",
                            data=output_zip,
                            file_name=f'processed_{uploaded_file_name[:-4]}.zip')
