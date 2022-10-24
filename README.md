[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/sjskoko/dart_pdf_bounding_box-task/main/pdf_bbox_app.py)

# dart_PDF_bounding_box-task
This project will be used for object detection task. 

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
