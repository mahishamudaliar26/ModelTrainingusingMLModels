import os  
import pandas as pd  
from azure.ai.formrecognizer import DocumentAnalysisClient  
from azure.core.credentials import AzureKeyCredential  
from tabulate import tabulate  

# Azure credentials setup  
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

# Function to process PDF and store extracted data in a single text file  
def process_pdf_and_store_data(pdf_path, local_directory):  
    try:  
        document_analysis_client = DocumentAnalysisClient(endpoint=fr_endpoint, credential=AzureKeyCredential(fr_key))  
        print(f"Processing PDF: {pdf_path}")  
         
        with open(pdf_path, "rb") as pdf_file:  
            poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=pdf_file)  
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
        base_filename = os.path.basename(pdf_path).replace('.pdf', '')  
        combined_filename = f"{base_filename}_combined.txt"  
        combined_path = os.path.join(local_directory, combined_filename)  
 
        # Write combined data to file  
        with open(combined_path, 'w', encoding='utf-8') as file:  
            # Write text data  
            file.write("Extracted Text:\n")  
            file.write(text_data)  
            file.write("\n\n")  
 
            # Write table data  
            for idx, table_data in enumerate(tables_data):  
                file.write(f"Table {idx + 1}:\n")  
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
 
                # Convert DataFrame to markdown table format and write to file  
                table_markdown = tabulate(df.values, tablefmt="pipe")  
                file.write(table_markdown)  
                file.write("\n\n")  
 
        return combined_filename  
 
    except Exception as e:  
        print(f"Error processing {pdf_path}: {e}")  
        return None  

# Define input and output directories  
input_directory = r"C:\Users\MahishaMudaliar\Desktop\sentiment-analysis\Retail Chain - Wallmart - fy2023-walmart-esg-highlights.pdf"  
output_directory = r"C:\Users\MahishaMudaliar\Desktop\sentiment-analysis"  

# Ensure the output directory exists  
if not os.path.exists(output_directory):  
    os.makedirs(output_directory)  

# Check if input directory is a file or directory  
if os.path.isfile(input_directory):  
    # Process a single PDF file  
    combined_filename = process_pdf_and_store_data(input_directory, output_directory)  
    if combined_filename:  
        print(f"Combined text file '{combined_filename}' generated and stored locally.")  
else:  
    # Traverse the input directory and its subdirectories to find all PDF files  
    for root, dirs, files in os.walk(input_directory):  
        for file in files:  
            if file.endswith('.pdf'):  
                pdf_path = os.path.join(root, file)  
                combined_filename = process_pdf_and_store_data(pdf_path, output_directory)  
                if combined_filename:  
                    print(f"Combined text file '{combined_filename}' generated and stored locally.")  
