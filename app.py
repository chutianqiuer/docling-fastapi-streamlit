from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import time
import shutil
import pandas as pd
import json
import yaml
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.pipeline_options import PdfPipelineOptions

app = FastAPI()
_log = logging.getLogger(__name__)

# Configure PDF pipeline options
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 1.0  # Replace IMAGE_RESOLUTION_SCALE with a fixed value or variable
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

# Configure DocumentConverter
doc_converter = DocumentConverter(
    allowed_formats=[
        InputFormat.PDF,
        InputFormat.IMAGE,
        InputFormat.DOCX,
        InputFormat.HTML,
        InputFormat.PPTX,
        InputFormat.ASCIIDOC,
        InputFormat.MD,
    ],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=StandardPdfPipeline,
            backend=PyPdfiumDocumentBackend,
            pipeline_options=pipeline_options,
        ),
        InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
    },
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.post("/process/")
async def process_document(file: UploadFile = File(...)):
    """Endpoint to process uploaded documents."""
    start_time = time.time()

    try:
        # Save uploaded file to a temporary location
        input_file = OUTPUT_DIR / file.filename
        with input_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert document
        conv_res = doc_converter.convert(input_file)

        # Create output directory for this input
        doc_filename = conv_res.input.file.stem
        output_dir = OUTPUT_DIR / doc_filename
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save outputs (images, markdown, tables, etc.)
        for page_no, page in conv_res.document.pages.items():
            page_image_filename = output_dir / f"{doc_filename}-page-{page_no}.png"
            with page_image_filename.open("wb") as fp:
                page.image.pil_image.save(fp, format="PNG")

        # Save markdown with embedded pictures
        md_embedded_filename = output_dir / f"{doc_filename}-with-images.md"
        conv_res.document.save_as_markdown(md_embedded_filename, image_mode=ImageRefMode.EMBEDDED)

        # Save document as JSON
        json_filename = output_dir / f"{doc_filename}.json"
        with json_filename.open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(conv_res.document.export_to_dict(), indent=4))

        # Save tables as CSV
        for table_ix, table in enumerate(conv_res.document.tables):
            table_df: pd.DataFrame = table.export_to_dataframe()
            table_csv_filename = output_dir / f"{doc_filename}-table-{table_ix+1}.csv"
            table_df.to_csv(table_csv_filename, index=False)

        # Cleanup and response
        end_time = time.time() - start_time
        return {
            "message": "File processed successfully",
            "processing_time": f"{end_time:.2f} seconds",
            "output_directory": str(output_dir),
        }

    except Exception as e:
        _log.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Endpoint to download processed files."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8010, reload=True)
