import urllib
import gzip
from zipfile import ZipFile
import shutil
import boto3
import os
import pandas as pd


def download_url(url, directory=os.getcwd(), remove_zip=True):
    ext = url.split(".")[-1]
    name = url.split("/")[-1]
    file_path = os.path.join(directory, name)
    try:
        # Download file
        print("Downloading " + url)
        with urllib.request.urlopen(url) as r:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(r, f)
                f.seek(0)

        # Unzip & save
        orig_path = file_path
        if ext=="gz":
            print("Unzipping " + file_path)
            with gzip.open(file_path, 'rb') as f_in:
                with open(file_path[:-3], 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file_path = file_path[:-3]
            if remove_zip: os.remove(orig_path)
        elif ext=="zip":
            print("Unzipping " + file_path)
            with ZipFile(file_path, 'r') as zip_ref:
                extracted = zip_ref.namelist()
                zip_ref.extractall(directory)
            file_path = [os.path.join(directory, f) for f in extracted]
            if remove_zip: os.remove(orig_path)
        
        return(file_path)
    except:
        print("Failed: " + file_path)

def upload_files_to_s3(file_paths, keys=None, s3_path=None, bucket="dataidealist"):
    file_paths = [file_paths] if isinstance(file_paths, str) else file_paths
    if keys is None: keys = [f.split("/")[-1] for f in file_paths]
    if s3_path: keys = [os.path.join(s3_path, k) for k in keys]
    responses = []
    s3_client = boto3.client('s3')
    for f, k in zip(file_paths, keys):
        print("Uploading to S3: " + f + " as " + k)
        responses.append(s3_client.upload_file(f, bucket, k))
    return(responses, keys)

def upload_folder_to_s3(directory, s3_path=None, bucket="dataidealist"):
    with os.scandir(directory) as entries:
        files = [entry.is_file() for entry in entries]
        entries = entries[files]
        files = [os.path.join(directory, entry) for entry in entries]
        responses, keys = upload_files_to_s3(files, s3_path=s3_path, bucket=bucket)
    return(responses, keys)

def upload_urls_to_s3(urls, bucket="dataidealist"):
    urls = [urls] if isinstance(urls, str) else urls
    download_paths = [download_url(url) for url in urls]
    file_paths = []
    for i in download_paths:
        if hasattr(i, '__iter__'):
            for j in i:
                file_paths.append(j)
        else:
            file_paths.append(i)
    responses, keys = upload_files_to_s3(file_paths, bucket=bucket)
    return(responses, keys)

def download_from_s3(key, filename=None, directory=os.getcwd(), bucket="dataidealist"):
    if filename is None: filename=key
    file_path = os.path.join(directory, filename)
    s3 = boto3.client('s3')
    s3.download_file(bucket, key, file_path)

def datasets(name="mhc1", save_to_csv=False):
    if name=="mhc1":
        filename = "./data/mhc1/bdata.20130222.mhci.txt"
        if not os.path.isfile(filename): download_from_s3("bdata.20130222.mhci.txt", "./data/mhc1/bdata.20130222.mhci.txt")
        data = pd.read_csv(filename, delimiter="\t")
        sel = data[(data["species"]=="human") & (data["inequality"]=="=")]
        if save_to_csv: sel[["sequence","meas"]].to_csv("./data/mhc1/bdata.20130222.mhci.csv")
        seq = sel["sequence"].tolist()
        val = sel["meas"].tolist()
    return(seq, val, data)