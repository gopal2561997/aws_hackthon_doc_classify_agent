# agent1.py - Uploads document to S3, extracts content, populates Neo4j
import boto3
import fitz  # PyMuPDF
import json
import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import base64
import mimetypes
from neo4j import GraphDatabase
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_aws import ChatBedrock
import tempfile
import io


load_dotenv()

# AWS and Neo4j config
S3_BUCKET = os.getenv("S3_BUCKET")
REGION = os.getenv("REGION")



def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])
 
def extract_text_from_image(file, media_type):
    image_bytes = file.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": image_base64
        }
    }
 
def extract_data(file, filetype):
    file.seek(0)  # Reset stream for each processing
    if filetype == "pdf":
        return extract_text_from_pdf(file)
 
    elif filetype in ["jpg", "jpeg", "png"]:
        media_type = mimetypes.types_map.get(f".{filetype}", "image/jpeg")
        return extract_text_from_image(file, media_type)
 
    elif filetype == "csv":
        df = pd.read_csv(file)
        return df.to_json(orient="records")
 
    elif filetype in ["xls", "xlsx"]:
        df = pd.read_excel(file)
        return df.to_json(orient="records")
 
    elif filetype == "txt":
        return file.read().decode("utf-8")
 
    elif filetype == "json":
        json_data = json.load(file)
        return json.dumps(json_data, indent=2)
 
    else:
        return None



def process_document_and_upload_to_s3(uploaded_file, filetype):
    print("Process Document")
    # AWS and Neo4j config
    S3_BUCKET = os.getenv("S3_BUCKET")
    REGION = os.getenv("REGION")

    # Initialize S3 client
    s3 = boto3.client("s3", region_name=REGION)

    # Determine appropriate suffix for temporary file
    suffix_map = {
        "pdf": ".pdf",
        "jpg": ".jpg",
        "jpeg": ".jpeg",
        "png": ".png",
        "csv": ".csv",
        "excel": ".xlsx",
        "txt": ".txt",
        "json": ".json"
    }
    suffix = suffix_map.get(filetype.lower(), "")

    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    # Generate unique filename and S3 key
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = uploaded_file.name
    folder_name = "doc_main/"
    file_key = f"{folder_name}{filename}_{current_time}"

    # Upload file to S3
    print("Upload Doc:",file_key)
    s3.upload_file(tmp_file_path, S3_BUCKET, filename)
    # Download file from S3
    print("Uploaded")
    response = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
    s3_file = response['Body'].read()
    file_stream = io.BytesIO(s3_file)
    file_stream.seek(0)

    # Extract data from the file
    print("Data Extract")
    doc_data = extract_data(file_stream,filetype)
    #parsed_schema=prepare_json_schema_for_neo4j(doc_data)
    # Save parsed schema as JSON locally
    json_folder_path = r'C:\Users\gasaramm\Documents\AWS_Hankathon\Data'
    os.makedirs(json_folder_path, exist_ok=True)
    #json_file_name = f"{filename}_{current_time}.json"
    #local_json_path = os.path.join(json_folder_path, json_file_name)

    '''with open(local_json_path, "w") as json_file:
        json.dump(parsed_schema, json_file, indent=4)'''

    # Upload JSON to S3
    #json_file_key = f"{folder_name}{json_file_name}"
    #s3.upload_file(local_json_path, S3_BUCKET, json_file_key)

    # Upload parsed data to Neo4j
    '''neoa4j_py_script=prepare_python_script_for_neo4j(json_schema)
    with open("neo4j_config.py", "w") as f:
        f.write(neoa4j_py_script)'''
    return "Uploaded to S3, parsed, and pushed to Neo4j."

