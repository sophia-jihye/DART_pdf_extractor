import os
from tqdm import tqdm
import pdfplumber

from util import *
from caption_module.caption_extraction import *


class Extractor():
    def __init__(self, args):
        # with file_name
        self.pdf_dir = args.pdf_dir
        self.save_dir = args.save_dir

        # get pdf name and path
        self.file_paths = get_file_paths(args.pdf_dir)
        self.file_names = get_file_names(args.pdf_dir)

        # make sub output dir
        self.cropped_text_save_dir = None
        self.cropped_image_save_dir = None
        self.cropped_table_save_dir = None
        self.cropped_caption_save_dir = None
        self.page_image_save_dir = None

        # make super save directory
        if self.save_dir is not None:
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)

        # loop each pdf
        for pdf_name in self.file_names:

            sub_path = os.path.join(self.save_dir, pdf_name[:-4])
            if not os.path.exists(sub_path):
                os.mkdir(sub_path)


            # generate crop image dir
            if args.crop == True:
                if args.text == True:
                    cropped_text_save_dir = os.path.join(sub_path, 'cropped_text')

                    if not os.path.exists(cropped_text_save_dir):
                        os.mkdir(cropped_text_save_dir)

                if args.image == True:
                    cropped_image_save_dir = os.path.join(sub_path, 'cropped_image')

                    if not os.path.exists(cropped_image_save_dir):
                        os.mkdir(cropped_image_save_dir)

                if args.table == True:
                    cropped_table_save_dir = os.path.join(sub_path, 'cropped_table')

                    if not os.path.exists(cropped_table_save_dir):
                        os.mkdir(cropped_table_save_dir)

                if args.image == True:
                    cropped_caption_save_dir = os.path.join(sub_path, 'cropped_caption')

                    if not os.path.exists(cropped_caption_save_dir):
                        os.mkdir(cropped_caption_save_dir)

            # generate page image dir
            if args.page_image == True:    
                page_image_save_dir = os.path.join(sub_path, 'page_image')

                if not os.path.exists(page_image_save_dir):
                    os.mkdir(page_image_save_dir)



        # save argparser
        self.args = args

    def page_to_table_object(self, page):
        return page.find_tables(table_settings={'vertical_strategy': 'lines', 'horizontal_strategy': 'lines'})

    def page_to_image_object(self, page):
        return page.images
        
    def page_to_text_object(self, page):
        return page.extract_words()

    def table_object_to_bbox(self, table_objects):
        return [i.bbox for i in table_objects]

    def image_object_to_bbox(self, img_objects, page):
        return [(image['x0'], page.height - image['y1'], image['x1'], page.height - image['y0']) for image in img_objects]

    def text_object_to_bbox(self, text_objects, page): # 사용 x
        return [(text['x0'], page.height - text['y1'], text['x1'], page.height - text['y0']) for text in text_objects]


    def table_extractor(self, table_objects, im):

        if table_objects:
            table_bbox_list = [i.bbox for i in table_objects]
            # print(j, 'page Table', table_bbox_list)
            for bbox in bbox_padding(table_bbox_list):
                im.draw_rect(bbox, fill=(255, 0, 0, 30))
        
        return im
    
    def image_extractor(self, img_objects, im, page):

        if img_objects:
            img_bbox_list = [(image['x0'], page.height - image['y1'], image['x1'], page.height - image['y0']) for image in img_objects]
            # print(j, 'page Image', img_bbox_list)
            for bbox in bbox_padding(img_bbox_list):
                im.draw_rect(bbox, fill=(255, 255, 0, 30))

        return im

    def caption_extractor(self, page, im, image_object, table_object, text_object, threshold_caption_image=100, threshold_caption_table=30, threshold_chunk=45, threshold_line_1=11, threshold_line_2=21, resolution=400, check=False):
        '''
        pages: get_pages(pdf)의 결과물
        image_object, table_object, text_object: pdfplumber로 추출한 image, table, text 정보
        corp: 결과를 저장할 폴더 이름 (str)
        threshold_caption_image: 해당 텍스트가 특정 키워드를 포함하는 경우 표/이미지의 캡션에 해당하는지 아닌지 구분하는 threshold (거리) (image에 대한 캡션 추출 시)
        threshold_caption_table: 해당 텍스트가 특정 키워드를 포함하는 경우 표/이미지의 캡션에 해당하는지 아닌지 구분하는 threshold (거리) (table에 대한 캡션 추출 시)
        threshold_chunk: 같은 줄에 있을 때 같은 chunk인지 아닌지 구분하는 threshold (거리)
        threshold_line_1: 한 문장이 다음 줄로 이어지는 것인지 아닌지 구분하는 threshold (y값 거리)
        threshold_line_2: 지금까지 인식한 마지막 캡션의 다음 텍스트 토큰이 특정 키워드를 포함하는 경우 해당 토큰이 이어지는 캡션인지 아닌지 구분하는 threshold (y값 거리)
        check: False이면 모든 페이지에 대한 결과를 이미지 파일로 저장, json 파일도 저장
            int값(1부터 시작, 저장되는 이미지 파일 이름과 같은 값)이면 해당 페이지에 대한 결과만 이미지 파일로 저장 (check 폴더에), json 파일은 저장 x

        output: 페이지별로 캡션의 bounding box가 표시된 이미지 파일 + 추출한 캡션을 텍스트로 저장한 json 파일
        '''
        result = {} # 추출한 캡션을 텍스트로 저장할 dictionary

        result['image'] = []
        result['table'] = []

        # image에 대한 캡션 추출
        if (check == False) and len(image_object) != 0:
            image_data = image_object
            text_data = text_object
            image_bb_to_draw = []
            i_text_bb_to_draw = []
            i_text_contents = []

            for image in image_data:
                image_bb_to_draw.append(get_bbox(image))
                caption_bb_for_this_image = []
                caption_text_for_this_image = []

                i = 0
                while i < len(text_data):
                    # 조건 1: 특정 키워드를 포함 (표 위/아래에 있는 경우 구분) + image와의 거리가 threshold_caption_image 이내 + 텍스트가 표에 포함되지 않음 (캡션의 시작점)
                    # 표 위 정규표현식: (kk기준일 / (nnnn.
                    # 표 아래 정규표현식: 주n) / *n / e)
                    if rect_distance(get_bbox(image), get_bbox(text_data[i])) <= threshold_caption_image \
                    and ((top_or_bottom(get_bbox(image), get_bbox(text_data[i])) == -1 and any(x in text_data[i]['text'] for x in ['[', '<', '단위', '(당기'])) \
                    or (top_or_bottom(get_bbox(image), get_bbox(text_data[i])) == -1 and re.search("^\([가-힣]*기준일|^\([0-9]{4}\.", text_data[i]['text'])) \
                    or (top_or_bottom(get_bbox(image), get_bbox(text_data[i])) == 1 and any(x in text_data[i]['text'] for x in ['※', '■', '☞', '[', '출처'])) \
                    or (top_or_bottom(get_bbox(image), get_bbox(text_data[i])) == 1 and re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']))) \
                    and contains(get_bbox(image), get_bbox(text_data[i])) == False:
                        # print('condition 1: detected start of caption')
                        caption_bb_for_this_image.append(get_bbox(text_data[i]))
                        caption_text_element = []
                        caption_text_element.append(text_data[i]['text'])
                        i += 1

                        while True:
                            # 조건 2: 앞 토큰과 같은 줄 + 거리가 threshold_chunk 이내 + 텍스트가 표에 포함되지 않음
                            if get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3] \
                            and rect_distance(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_chunk \
                            and contains(get_bbox(image), get_bbox(text_data[i])) == False:
                                # print('condition 2 - same line, same chunk')
                                caption_bb_for_this_image.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 3: 줄이 바뀌지만 높이 차이가 threshold_line_1 이내 + 텍스트가 표에 포함되지 않음 (이어지는 문장으로 판단) 
                            elif diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_1 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(get_bbox(image), get_bbox(text_data[i])) == False:
                                # print('condition 3 - different line, same chunk')
                                caption_bb_for_this_image.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 4: 줄이 바뀌고 바로 다음 텍스트가 특정 정규표현식과 매치 + 높이 차이가 threshold_line_2 이내 + 텍스트가 표에 포함되지 않음
                            # 정규표현식: 주n) / *n / e)
                            elif re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']) \
                            and diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_2 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(get_bbox(image), get_bbox(text_data[i])) == False:
                                # print('condition 4 - different line, still caption')
                                caption_bb_for_this_image.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            else:
                                # print('end of caption')
                                break

                        caption_text_for_this_image.append(caption_text_element)
                        
                    else:
                        i += 1

                i_text_bb_to_draw.append(caption_bb_for_this_image)
                i_text_contents.append(caption_text_for_this_image)

        # table에 대한 캡션 추출
        if (check == False) and len(table_object) != 0:
            table_data = table_object
            text_data = text_object
            table_bb_to_draw = []
            t_text_bb_to_draw = []
            t_text_contents = []

            for table in table_data:
                table_bb_to_draw.append(table.bbox)
                caption_bb_for_this_table = []
                caption_text_for_this_table = []

                i = 0
                while i < len(text_data):
                    # 조건 1: 특정 키워드를 포함 (표 위/아래에 있는 경우 구분) + table과의 거리가 threshold_caption_table 이내 + 텍스트가 표에 포함되지 않음 (캡션의 시작점)
                    # 표 위 정규표현식: (kk기준일 / (nnnn.
                    # 표 아래 정규표현식: 주n) / *n / e)
                    if rect_distance(table.bbox, get_bbox(text_data[i])) <= threshold_caption_table \
                    and ((top_or_bottom(table.bbox, get_bbox(text_data[i])) == -1 and any(x in text_data[i]['text'] for x in ['[', '<', '단위', '(당기'])) \
                    or (top_or_bottom(table.bbox, get_bbox(text_data[i])) == -1 and re.search("^\([가-힣]*기준일|^\([0-9]{4}\.", text_data[i]['text'])) \
                    or (top_or_bottom(table.bbox, get_bbox(text_data[i])) == 1 and any(x in text_data[i]['text'] for x in ['※', '■', '☞', '[', '출처'])) \
                    or (top_or_bottom(table.bbox, get_bbox(text_data[i])) == 1 and re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']))) \
                    and contains(table.bbox, get_bbox(text_data[i])) == False:
                        # print('condition 1: detected start of caption')
                        caption_bb_for_this_table.append(get_bbox(text_data[i]))
                        caption_text_element = []
                        caption_text_element.append(text_data[i]['text'])
                        i += 1

                        while True:
                            # 조건 2: 앞 토큰과 같은 줄 + 거리가 threshold_chunk 이내 + 텍스트가 표에 포함되지 않음
                            if get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3] \
                            and rect_distance(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_chunk \
                            and contains(table.bbox, get_bbox(text_data[i])) == False:
                                # print('condition 2 - same line, same chunk')
                                caption_bb_for_this_table.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 3: 줄이 바뀌지만 높이 차이가 threshold_line_1 이내 + 텍스트가 표에 포함되지 않음 (이어지는 문장으로 판단) 
                            elif diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_1 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(table.bbox, get_bbox(text_data[i])) == False:
                                # print('condition 3 - different line, same chunk')
                                caption_bb_for_this_table.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 4: 줄이 바뀌고 바로 다음 텍스트가 특정 정규표현식과 매치 + 높이 차이가 threshold_line_2 이내 + 텍스트가 표에 포함되지 않음
                            # 정규표현식: 주n) / *n / e)
                            elif re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']) \
                            and diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_2 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(table.bbox, get_bbox(text_data[i])) == False:
                                # print('condition 4 - different line, still caption')
                                caption_bb_for_this_table.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            else:
                                # print('end of caption')
                                break

                        caption_text_for_this_table.append(caption_text_element)
                        
                    else:
                        i += 1

                t_text_bb_to_draw.append(caption_bb_for_this_table)
                t_text_contents.append(caption_text_for_this_table)

        # 결과 저장
        if (check == False) and (len(image_object) != 0 or len(table_object) != 0):    

            if len(image_object) != 0:
                for j in range(len(image_bb_to_draw)):
                    # im.draw_rect(image_bb_to_draw[j], fill=(255, 255, 0, 30))
                    im.draw_rects(i_text_bb_to_draw[j])
                    # print(f'(p.{p+1}) caption for image:', [' '.join(each_caption) for each_caption in i_text_contents[j]])
                    result['image'].append([' '.join(each_caption) for each_caption in i_text_contents[j]])

            if len(table_object) != 0:
                for j in range(len(table_bb_to_draw)):
                    # im.draw_rect(table_bb_to_draw[j], fill=(255, 0, 0, 30))
                    im.draw_rects(t_text_bb_to_draw[j])
                    # print(f'(p.{p+1}) caption for table:', [' '.join(each_caption) for each_caption in t_text_contents[j]])
                    result['table'].append([' '.join(each_caption) for each_caption in t_text_contents[j]])

            # if check == False:
            #     # 결과를 저장할 디렉터리가 없으면 디렉터리 생성
            #     if not os.path.exists(f'result/{corp}'):
            #         os.makedirs(f'result/{corp}') 
            #     im.save(f'result/{corp}/{p+1}.png', format="PNG")

            # else:
            #     # 결과를 저장할 디렉터리가 없으면 디렉터리 생성
            #     if not os.path.exists(f'result/check'):
            #         os.makedirs(f'result/check') 
            #     im.save(f'result/check/{p+1}.png', format="PNG")

        # if check == False:
        #     with open(f'result/{corp}/result.json', 'w') as f: json.dump(result, f, indent="\t", ensure_ascii=False)

        return im, result
    
    def create_bbox_with_img_save(self):

        pdf_file_paths = self.file_paths
        pdf_file_lists = self.file_names
        save_path = self.save_dir

        text_is_true = self.args.text
        table_is_true = self.args.table
        image_is_true = self.args.image
        caption_is_true = self.args.caption
        


        pdf_dict = {}

        ## loop of saving img
        for i in range(len(pdf_file_lists)):
            # i is pdf num

            page_img_list =[]

            # define pdf object
            pdf = pdfplumber.open(pdf_file_paths[i]) # open ith file
            pages = pdf.pages # define each page

            # define pdf name
            file_name = pdf_file_lists[i]
            print(f'process {file_name}')

            # define sub save directory for output 
            pdf_save_directory = save_path + '/' + file_name[:-4]

            ## loop of each page
            for j in tqdm(range(len(pages))):
                # j is page num
                
                page = pages[j]
                page_height = page.height

                im = page.to_image(resolution=400)
                table_objects = self.page_to_table_object(page)
                image_objects = self.page_to_image_object(page)
                text_objects = self.page_to_text_object(page)

                # extract text
                if text_is_true == True:
                    if self.args.crop == True:
                        only_text = [''.join(i['text']) for i in text_objects]
                        with open(os.path.join(pdf_save_directory, 'cropped_text', f'page{j}.txt'), 'w', encoding='UTF-8') as f:
                            f.write(' '.join(only_text))

                # extract table
                if table_is_true == True:
                    if self.args.page_image == True:
                        im = self.table_extractor(table_objects, im)
                    if self.args.crop == True:
                        table_bboxs = self.table_object_to_bbox(table_objects)
                        for table_num, table_bbox in enumerate(table_bboxs):
                            crop_table_im = page.crop(table_bbox).to_image(resolution=200)
                            crop_table_im.save(os.path.join(pdf_save_directory, 'cropped_table', f'page{j}_table{table_num}.png'))
                    
                # extract image
                if image_is_true == True:
                    if self.args.page_image == True:
                        im = self.image_extractor(image_objects, im, page)
                    if self.args.crop == True:
                        image_bboxs = self.image_object_to_bbox(image_objects, page)
                        for image_num, image_bbox in enumerate(image_bboxs):
                            crop_image_im = page.crop(image_bbox).to_image(resolution=200)
                            crop_image_im.save(os.path.join(pdf_save_directory, 'cropped_image', f'page{j}_image{image_num}.png'))
                
                # extract caption
                if caption_is_true == True:
                    if self.args.page_image == True:
                        im, caption_info = self.caption_extractor(page, im, image_objects, table_objects, text_objects)
                    

                # append page image to page_img_list
                page_img_list.append(im)

                # save page image with extracted object
                if save_path is not None:
                    os.path.join(pdf_save_directory, 'page_image', f'page{j}.png')
                    im.save(os.path.join(pdf_save_directory, 'page_image', f'page{j}.png'), format='PNG')

                if self.args.crop == True and self.args.caption == True:
                    # with open(os.path.join(pdf_save_directory, 'cropped_caption', f'{str(j)}.json'), 'w', encoding='UTF-8') as f: 
                    #     json.dump(caption_info, f, indent="\t", ensure_ascii=False)
                    if self.args.table == True:
                        for table_num, table_txt in enumerate(caption_info['table']):
                            with open(os.path.join(pdf_save_directory, 'cropped_caption', f'page{j}_table{table_num}.txt'), 'w', encoding='UTF-8') as f:
                                f.write('\n'.join(table_txt))

                    if self.args.image == True:
                        for image_num, image_txt in enumerate(caption_info['image']):
                            with open(os.path.join(pdf_save_directory, 'cropped_caption', f'page{j}_image{image_num}.txt'), 'w', encoding='UTF-8') as f:
                                f.write('\n'.join(image_txt))




            pdf_dict[pdf_file_paths[i]] = page_img_list


        return pdf_dict