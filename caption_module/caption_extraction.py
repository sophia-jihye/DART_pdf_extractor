import os
import re
import json
from math import dist
from tqdm.notebook import tqdm


# 2개의 직사각형 사이의 최단거리 계산
# rotation은 고려 x
# https://stackoverflow.com/questions/4978323/how-to-calculate-distance-between-two-rectangles-context-a-game-in-lua
def rect_distance(RectA, RectB):
    A_x0, A_y0, A_x1, A_y1 = RectA
    B_x0, B_y0, B_x1, B_y1 = RectB
    
    # 변수명: A 기준
    left = B_x1 < A_x0 
    right = A_x1 < B_x0
    top = A_y1 < B_y0
    bottom = B_y1 < A_y0
    
    if top and left:
        return dist((A_x0, A_y1), (B_x1, B_y0))
    elif left and bottom:
        return dist((A_x0, A_y0), (B_x1, B_y1))
    elif bottom and right:
        return dist((A_x1, A_y0), (B_x0, B_y1))
    elif right and top:
        return dist((A_x1, A_y1), (B_x0, B_y0))
    elif left:
        return A_x0 - B_x1
    elif right:
        return B_x0 - A_x1
    elif bottom:
        return A_y0 - B_y1
    elif top:
        return B_y0 - A_y1
    else: # rectangles intersect
        return 0.0

# # 2개의 직사각형 상하관계만 판단
def top_or_bottom(RectA, RectB):
    _, A_y0, _, A_y1 = RectA
    _, B_y0, _, B_y1 = RectB
    
    # 변수명: A 기준
    top = A_y1 < B_y0
    bottom = B_y1 < A_y0

    # A가 위에 있음
    if top == True and bottom == False:
        return 1
    # B가 위에 있음
    elif top == False and bottom == True:
        return -1
    # 2개의 직사각형이 intersect
    else:
        return 0

# y값의 차이만 계산 (수직 거리)
# rect_distance에서 A와 B의 x0과 x1은 같은 경우
def diff_height(RectA, RectB):
    _, A_y0, _, A_y1 = RectA
    _, B_y0, _, B_y1 = RectB

    # 변수명: A 기준
    top = A_y1 < B_y0
    bottom = B_y1 < A_y0

    # A가 위에 있음
    if top == True and bottom == False:
        return B_y0 - A_y1
    # B가 위에 있음
    elif top == False and bottom == True:
        return A_y0 - B_y1
    # 2개의 직사각형이 intersect
    else:
        return 0.0

# RectA가 RectB를 포함하는지 체크
# https://stackoverflow.com/questions/21275714/check-rectangle-inside-rectangle-in-python
def contains(RectA, RectB):
    A_x0, A_y0, A_x1, A_y1 = RectA
    B_x0, B_y0, B_x1, B_y1 = RectB

    return A_x0 < B_x0 < B_x1 < A_x1 and A_y0 < B_y0 < B_y1 < A_y1

# image, text에서 사용
def get_bbox(obj):
    bbox = (round(obj['x0'], 2), round(obj['top'], 2), round(obj['x1'], 2), round(obj['bottom'], 2))
    return bbox

# 캡션을 추출하는 함수
def caption_detector(pages, corp_image, corp_table, corp_text, corp, threshold_caption_image=100, threshold_caption_table=30, threshold_chunk=45, threshold_line_1=11, threshold_line_2=21, resolution=400, check=False):
    '''
    pages: get_pages(pdf)의 결과물
    corp_image, corp_table, corp_text: pdfplumber로 추출한 image, table, text 정보
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

    for p in tqdm(range(len(pages))):
        result[p] = {}
        result[p]['image'] = []
        result[p]['table'] = []

        # image에 대한 캡션 추출
        if (check == False or p+1 == check) and len(corp_image[p]) != 0:
            image_data = corp_image[p]
            text_data = corp_text[p]
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
        if (check == False or p+1 == check) and len(corp_table[p]) != 0:
            table_data = corp_table[p]
            text_data = corp_text[p]
            table_bb_to_draw = []
            t_text_bb_to_draw = []
            t_text_contents = []

            for table in table_data:
                table_bb_to_draw.append(table['bbox'])
                caption_bb_for_this_table = []
                caption_text_for_this_table = []

                i = 0
                while i < len(text_data):
                    # 조건 1: 특정 키워드를 포함 (표 위/아래에 있는 경우 구분) + table과의 거리가 threshold_caption_table 이내 + 텍스트가 표에 포함되지 않음 (캡션의 시작점)
                    # 표 위 정규표현식: (kk기준일 / (nnnn.
                    # 표 아래 정규표현식: 주n) / *n / e)
                    if rect_distance(table['bbox'], get_bbox(text_data[i])) <= threshold_caption_table \
                    and ((top_or_bottom(table['bbox'], get_bbox(text_data[i])) == -1 and any(x in text_data[i]['text'] for x in ['[', '<', '단위', '(당기'])) \
                    or (top_or_bottom(table['bbox'], get_bbox(text_data[i])) == -1 and re.search("^\([가-힣]*기준일|^\([0-9]{4}\.", text_data[i]['text'])) \
                    or (top_or_bottom(table['bbox'], get_bbox(text_data[i])) == 1 and any(x in text_data[i]['text'] for x in ['※', '■', '☞', '[', '출처'])) \
                    or (top_or_bottom(table['bbox'], get_bbox(text_data[i])) == 1 and re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']))) \
                    and contains(table['bbox'], get_bbox(text_data[i])) == False:
                        # print('condition 1: detected start of caption')
                        caption_bb_for_this_table.append(get_bbox(text_data[i]))
                        caption_text_element = []
                        caption_text_element.append(text_data[i]['text'])
                        i += 1

                        while True:
                            # 조건 2: 앞 토큰과 같은 줄 + 거리가 threshold_chunk 이내 + 텍스트가 표에 포함되지 않음
                            if get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3] \
                            and rect_distance(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_chunk \
                            and contains(table['bbox'], get_bbox(text_data[i])) == False:
                                # print('condition 2 - same line, same chunk')
                                caption_bb_for_this_table.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 3: 줄이 바뀌지만 높이 차이가 threshold_line_1 이내 + 텍스트가 표에 포함되지 않음 (이어지는 문장으로 판단) 
                            elif diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_1 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(table['bbox'], get_bbox(text_data[i])) == False:
                                # print('condition 3 - different line, same chunk')
                                caption_bb_for_this_table.append(get_bbox(text_data[i]))
                                caption_text_element.append(text_data[i]['text'])
                                i += 1

                            # 조건 4: 줄이 바뀌고 바로 다음 텍스트가 특정 정규표현식과 매치 + 높이 차이가 threshold_line_2 이내 + 텍스트가 표에 포함되지 않음
                            # 정규표현식: 주n) / *n / e)
                            elif re.search("^주[0-9]*\)|\*[0-9]*|^[a-z]\)", text_data[i]['text']) \
                            and diff_height(get_bbox(text_data[i]), get_bbox(text_data[i-1])) <= threshold_line_2 \
                            and not (get_bbox(text_data[i])[1] == get_bbox(text_data[i-1])[1] and get_bbox(text_data[i])[3] == get_bbox(text_data[i-1])[3]) \
                            and contains(table['bbox'], get_bbox(text_data[i])) == False:
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
        if (check == False or p+1 == check) and (len(corp_image[p]) != 0 or len(corp_table[p]) != 0):    
            im = pages[p].to_image(resolution=resolution)
            im.reset()

            if len(corp_image[p]) != 0:
                for j in range(len(image_bb_to_draw)):
                    im.draw_rect(image_bb_to_draw[j], fill=(255, 255, 0, 30))
                    im.draw_rects(i_text_bb_to_draw[j])
                    print(f'(p.{p+1}) caption for image:', [' '.join(each_caption) for each_caption in i_text_contents[j]])
                    result[p]['image'].append([' '.join(each_caption) for each_caption in i_text_contents[j]])

            if len(corp_table[p]) != 0:
                for j in range(len(table_bb_to_draw)):
                    im.draw_rect(table_bb_to_draw[j], fill=(255, 0, 0, 30))
                    im.draw_rects(t_text_bb_to_draw[j])
                    print(f'(p.{p+1}) caption for table:', [' '.join(each_caption) for each_caption in t_text_contents[j]])
                    result[p]['table'].append([' '.join(each_caption) for each_caption in t_text_contents[j]])

            if check == False:
                # 결과를 저장할 디렉터리가 없으면 디렉터리 생성
                if not os.path.exists(f'result/{corp}'):
                    os.makedirs(f'result/{corp}') 
                im.save(f'result/{corp}/{p+1}.png', format="PNG")

            else:
                # 결과를 저장할 디렉터리가 없으면 디렉터리 생성
                if not os.path.exists(f'result/check'):
                    os.makedirs(f'result/check') 
                im.save(f'result/check/{p+1}.png', format="PNG")

    if check == False:
        with open(f'result/{corp}/result.json', 'w') as f: json.dump(result, f, indent="\t", ensure_ascii=False)