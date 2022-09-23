[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/sjskoko/dart_pdf_bounding_box-task/main/pdf_bbox_app.py)

# DARTPlumber: DART pdf object extractor
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
1. img_file\[미래에셋대우스팩3호]분기보고서(2022.05.03)\[미래에셋대우스팩3호]분기보고서(2022.05.03)_31.png -> 해당 파일에서 표는 감지되지만, 단락(paragraph)이 포함된 상자는 감지하지 못함
2. bounding box 너비를 조절하여 위아래 캡션/제목 추출기능
3. 이미지/표 개수 요약 파일 추가 

## Contact
SNUDM Homepage : http://dm.snu.ac.kr
