from pdf2jpg import pdf2jpg


inputpath = r"sample_pdf_file\[삼성바이오로직스]사업보고서(2022.03.21).pdf"
outputpath = r""
result = pdf2jpg.convert_pdf2jpg(inputpath,outputpath, pages="ALL")


import aspose.slides as slides
import aspose.pydrawing as drawing

with slides.Presentation() as presentation:
    presentation.slides.remove_at(0)
    presentation.slides.add_from_pdf(inputpath)
    for slide in presentation.slides:
        slide.get_thumbnail(2, 2).save("presentation_slide_{0}.jpg".format(str(slide.slide_number)), drawing.imaging.ImageFormat.jpeg)