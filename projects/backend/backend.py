import io
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import pandas as pd
from tabulate import tabulate
from azure.core.exceptions import ClientAuthenticationError , ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings

# Azure Form Recognizer configuration
fr_endpoint = "https://smrecog.cognitiveservices.azure.com/"
fr_key = "36ecfa2cb82d47a8b5d4c572ca8ef063"

# Function to check if a point is inside a polygon
def is_point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# Function to check if a bounding box is inside any table spans
def is_in_table(page_number, bounding_box):
    for table_span in table_spans:
        if table_span[0] == page_number and is_point_in_polygon(bounding_box[0], table_span[1]):
            return True
    return False

# Function to extract table data from Form Recognizer result
def extract_table_data(result):
    tables_data = []
    for table in result.tables:
        table_data = {}
        for cell in table.cells:
            row_index = cell.row_index
            col_index = cell.column_index
            if row_index not in table_data:
                table_data[row_index] = {}
            table_data[row_index][col_index] = cell.content
        tables_data.append(table_data)
    return tables_data

# Function to extract text data from Form Recognizer result
def extract_text_data(result):
    pages_text = {}
    for page in result.pages:
        page_text = ""
        for line in page.lines:
            if not is_in_table(page.page_number, line.polygon):
                text = line.content.decode("utf-8") if isinstance(line.content, bytes) else line.content
                page_text += text + " "  # Concatenate lines with a space
        pages_text[page.page_number] = page_text.strip()  # Strip trailing space

    # Combine text data with each page in a separate paragraph
    combined_text_data = "\n\n\n\n".join(pages_text.get(page_number, "") for page_number in sorted(pages_text))
    return combined_text_data

# Function to process PDF from Azure Blob Storage and store extracted data
def process_pdf_and_store_data_from_blob(blob_service_client, container_name, blob_name):
    try:
        # Get blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Download the PDF from blob storage
        pdf_data = blob_client.download_blob().readall()
        pdf_stream = io.BytesIO(pdf_data)

        document_analysis_client = DocumentAnalysisClient(endpoint=fr_endpoint, credential=AzureKeyCredential(fr_key))
        print(f"Processing PDF from Blob: {blob_name}")

        poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=pdf_stream)
        result = poller.result()

        # Extract table spans
        global table_spans
        table_spans = []
        for table in result.tables:
            for cell in table.cells:
                if cell.bounding_regions:
                    page_number = cell.bounding_regions[0].page_number
                    bounding_box = cell.bounding_regions[0].polygon
                    table_spans.append((page_number, bounding_box))

        tables_data = extract_table_data(result)
        text_data = extract_text_data(result)

        # Generate filename for the combined text file
        combined_filename = f"{os.path.splitext(blob_name)[0]}_combined.txt"

        # Write combined data to file
        combined_text = "Extracted Text:\n" + text_data + "\n\n"
        for idx, table_data in enumerate(tables_data):
            combined_text += f"Table {idx + 1}:\n"
            max_row = max(table_data.keys())
            max_col = max(max(row.keys() for row in table_data.values()))

            # Initialize the data array
            data = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]

            # Populate the data array with table content
            for row_idx, row_data in table_data.items():
                for col_idx, cell_content in row_data.items():
                    data[row_idx][col_idx] = cell_content

            # Convert the data array into a pandas DataFrame
            df = pd.DataFrame(data)

            # Convert DataFrame to markdown table format
            table_markdown = tabulate(df.values, tablefmt="pipe")
            combined_text += table_markdown + "\n\n"

        return combined_filename, combined_text

    except Exception as e:
        print(f"Error processing blob {blob_name}: {e}")
        return None, None

# Function to upload extracted text to Azure Blob Storage
def upload_extracted_text_to_blob(blob_service_client, container_name, blob_name, content):
    try:
        container_client = blob_service_client.get_container_client(container_name)
        # Create the container if it does not exist
        container_client.create_container()
    except ResourceExistsError:
        pass  # Container already exists

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(content, overwrite=True, content_settings=ContentSettings(content_type='text/plain'))

    print(f"Uploaded '{blob_name}' to container '{container_name}'")
