import os
from tqdm import tqdm

import pdfplumber

def listing_file_names(folder_path):
    if not os.path.exists(folder_path):
        folder_name = folder_path.split('/')[-1]
        exit(f'FolderNotExistError: There is no [{folder_name}] folder')

    ## list file name
    pdf_file_lists = os.listdir(folder_path)
    if not pdf_file_lists:
        exit('FileNotExistError: There are no files in the folder')
    
    return pdf_file_lists

def listing_file_paths(folder_path):

    ## list file name
    pdf_file_lists = listing_file_names(folder_path=folder_path)

    pdf_file_paths = [folder_path + '/' + file_name for file_name in pdf_file_lists]

    return pdf_file_paths

def bbox_padding(bbox_list, padding=0):
    new_bbox = []
    for bbox in bbox_list:
        new_bbox.append((bbox[0], max(bbox[1]-padding, 0), bbox[2], min(bbox[3]+padding, 842)))
    return new_bbox

def create_bbox_with_img_save(folder_path, save_path=None):

    pdf_file_lists = listing_file_names(folder_path=folder_path)
    pdf_file_paths = listing_file_paths(folder_path=folder_path)
    

    print('save is [' + str(save_path is not None) + ']')
    if save_path is not None:
        if not os.path.exists(save_path):
            os.makedirs(save_path)


    pdf_dict = {}

    ## loop of saving img
    for i in tqdm(range(len(pdf_file_lists))):

        page_img_list =[]

        pdf = pdfplumber.open(pdf_file_paths[i]) # open ith file
        pages = pdf.pages # define each page

        file_name = pdf_file_lists[i]

        if save_path is not None:
            pdf_save_directory = save_path + '/' + file_name[:-4]

            ## make directory for file
            if not os.path.exists(pdf_save_directory):
                os.makedirs(pdf_save_directory)

        ## loop of each page
        for j in range(min(30,len(pages))):
            
            page = pages[j]
            page_height = page.height

            table_objects = page.find_tables(table_settings={'vertical_strategy': 'lines', 'horizontal_strategy': 'lines'})
            img_objects = page.images
            im = page.to_image(resolution=400)

            if table_objects:
                table_bbox_list = [i.bbox for i in table_objects]
                print(j, 'page Table', table_bbox_list)
                for bbox in bbox_padding(table_bbox_list):
                    im.draw_rect(bbox, stroke='red')

            if img_objects:
                img_bbox_list = [(image['x0'], page_height - image['y1'], image['x1'], page_height - image['y0']) for image in img_objects]
                print(j, 'page Image', img_bbox_list)
                for bbox in bbox_padding(img_bbox_list):
                    im.draw_rect(bbox, stroke='blue')

            page_img_list.append(im)

            if save_path is not None:
                im.save(pdf_save_directory + '/' + file_name[:-4] + '_' + str(j) + '.png', format='PNG')

        pdf_dict[pdf_file_paths[i]] = page_img_list


    return pdf_dict

def get_text(page):
    text = page.extract_words()
    return text

def get_table(page):
    table = page.extract_tables()
    return table

def get_image(page):
    image = page.images





if __name__ == '__main__':
    folder_path = 'sample_pdf_file'
    save_path = 'sample_img_file'
    # img_dict = create_bbox_with_img_save(folder_path=folder_path, save_path=save_path)


    pdf_file_lists = listing_file_names(folder_path=folder_path)
    pdf_file_paths = listing_file_paths(folder_path=folder_path)


    print('save is [' + str(save_path is not None) + ']')
    if save_path is not None:
        if not os.path.exists(save_path):
            os.makedirs(save_path)


    pdf_dict = {}

    pdf = pdfplumber.open(pdf_file_paths[0])
    pages = pdf.pages
    page = pages[5]

    table = get_table(page)
    image = get_image(page)
    text = get_text(page)

    def bounding_box(dict):

        bbox = [dict['x0'], dict['y0'], dict['x1'], dict['y1']]
        text = '({}, {}), ({}, {})'.format(bbox)
        text += str(dict['x0'])
        text += ', '
        text += str(dict['y0'])
        text += '), ('
        text += str(dict['x1'])
        text += ', '
        text += str(dict['y1'])
        text += ')'
        return text
    for i in range(len(text)):
        print(text[i]['text'])
    print(text[0]['text'])
    print(bounding_box(text[0]))
