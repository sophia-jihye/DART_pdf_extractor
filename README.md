[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/sjskoko/dart_pdf_bounding_box-task/main/pdf_bbox_app.py)

<<<<<<< HEAD
# dart_PDF_bounding_box-task
This project will be used for object detection task. 

=======
# DART_pdf_bounding_box-task
This project will be used for DART pdf object detection task. 

## Installation
Clone this repo.
```sh
git clone https://github.com/snu-dm/DART_pdf_extractor.git
cd DART_pdf_extractor/
```
This code requires python 3+ and pdfplumber. Please Install dependencies by
```sh
pip install -r requirements.txt
```
## Getting Started
Use following parsers in your Linux terminal:
- table extraction (-t)
- image extraction (-i)
- caption extraction (-c)
- pdf_dir (-dir)
- save_dir (-save)
- croped_file_only (-crop)
- total_page_with_segmentation (-page_image) 

Below provides only table images with corresponding captions in jpeg and txt file respectively.
```sh
python main.py -t -c -crop
```


## Todo List
>>>>>>> parent of 5d22fc2 (Update README.md)
1. img_file\[미래에셋대우스팩3호]분기보고서(2022.05.03)\[미래에셋대우스팩3호]분기보고서(2022.05.03)_31.png -> 해당 파일에서 표는 감지되지만, 단락(paragraph)이 포함된 상자는 감지하지 못함

2. bounding box 너비를 조절하여 위아래 캡션/제목 추출기능

3. 이미지/표 개수 요약 파일 추가

### 220725 수정사항
streamlit 상에 설치된 ImageMagick의 policy.xml 수정이 필요

1. cloud 서버의 ImageMagick 설치 위치 찾기

2. 해당 위치에서 policy.xml 파일을 직접 수정
https://codechacha.com/ko/python-create-and-write-xml/
https://imagemagick.org/script/security-policy.php
https://stackoverflow.com/questions/52861946/imagemagick-not-authorized-to-convert-pdf-to-an-image

### 실행방법

> python main.py --table --image --caption

### 변경 사항

1. bbox 도출 함수(component 별)
2. im에 bbox 그려주는 함수
3. captioning component 별로 구분
4. bbox crop 해주는 함수
5. text 뽑아주는 함수
6. 