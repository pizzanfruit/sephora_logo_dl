import json
import os
import urllib.parse
import urllib.request
import psycopg2

import PIL
import requests
import xlrd
from azure.storage.blob import BlockBlobService, ContentSettings, PublicAccess
from bs4 import BeautifulSoup
from PIL import Image
from fix import resize

COUNT = 0


def main():
    directory = "sample_logo"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Download logos
    wb = xlrd.open_workbook("brands.xlsx")
    wb.sheet_names()
    sh = wb.sheet_by_index(0)
    brands = sh.col_values(0)
    with open("output.txt", "w") as output:
        for brand in brands:
            # save_logo(brand, directory, output)
            scrape_google_image(brand, directory, output)
    # Modify DB
    pg_dbname = os.environ["pg_dbname"]
    pg_user = os.environ["pg_user"]
    pg_host = os.environ["pg_host"]
    pg_password = os.environ["pg_password"]
    pg_connect_str = f"dbname='{pg_dbname}' user='{pg_user}' host='{pg_host}' " + \
        f"password='{pg_password}'"

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS MST_BRAND_LOGO(
	        BRAND_NAME		  						VARCHAR(255) PRIMARY KEY,
            LOGO_IMAGE_URL	                        VARCHAR(255) NOT NULL,    
            CREATE_TIMESTAMP                        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CREATE_USER                             VARCHAR(255) NOT NULL,
            UPDATE_TIMESTAMP                        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UPDATE_USER                             VARCHAR(255) NOT NULL
        );
    """
    insert_sql = """
        INSERT INTO MST_BRAND_LOGO(
	        BRAND_NAME, LOGO_IMAGE_URL, CREATE_TIMESTAMP, CREATE_USER, UPDATE_TIMESTAMP, UPDATE_USER
	        ) VALUES (%(brand_name)s, %(logo_image_url)s, current_timestamp, 'SYSTEM', current_timestamp, 'SYSTEM')
	        ON CONFLICT (BRAND_NAME)
	        DO UPDATE SET
		    LOGO_IMAGE_URL = %(logo_image_url)s;
    """
    try:
        conn = psycopg2.connect(pg_connect_str)
        cursor = conn.cursor()
    except Exception as e:
        print("Invalid dbname, user or password?")
        print(e)
        return
    cursor.execute(create_table_sql)
    # Upload to Azure Blob
    container_name = 'logos'
    block_blob_service = BlockBlobService(
        account_name=os.environ['azure_storage_account'], account_key=os.environ['azure_storage_key'])
    if not block_blob_service.exists(container_name):
        block_blob_service.create_container(
            container_name, public_access=PublicAccess.Container)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        fullname = os.path.join(directory, filename)
        brand, extension = os.path.splitext(filename)
        content_type = 'image/' + extension
        block_blob_service.create_blob_from_path(
            container_name,
            filename,
            fullname,
            content_settings=ContentSettings(content_type=content_type)
        )
        azure_logo_url = 'https://fsoftdtlp2diag974.blob.core.windows.net/' + \
            container_name + '/' + urllib.parse.quote(filename)
        cursor.execute(insert_sql, {'brand_name': brand,
                                    'logo_image_url': azure_logo_url})
        print(brand, azure_logo_url)
    conn.commit()
    cursor.close()
    conn.close()


def save_logo(brand, directory, output):
    output.write("\n")
    domain_endpoint = "https://company.clearbit.com/v1/domains/find?name=" + brand
    clearbit_api_key = os.environ["clearbit_api_key"]
    headers = {
        'Authorization': f'Bearer {clearbit_api_key}',
    }
    r = requests.get(domain_endpoint, headers=headers).json()
    global COUNT
    COUNT = COUNT + 1
    o1 = str(COUNT) + ". " + brand
    print(o1)
    output.write(o1)
    if 'error' in r:
        print(" >> No domain")
        output.write(" >> No domain")
        scrape_google_image(brand, directory, output)
        return
    domain_name = r['domain']
    image_endpoint = 'https://logo.clearbit.com/' + domain_name + "?size=800"
    print(" >> " + image_endpoint)
    output.write(" >> " + image_endpoint)
    try:
        image_file = directory + "/" + brand + ".png"
        urllib.request.urlretrieve(
            image_endpoint, image_file)
        resize(brand + ".png", directory, directory)
    except urllib.error.HTTPError:
        print(" >> No logo")
        output.write(" >> No logo")
        scrape_google_image(brand, directory, output)
        return


def scrape_google_image(brand, directory, output):
    global COUNT
    COUNT = COUNT + 1
    print(f"{COUNT}. Trying to get logo for {brand}")
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
    encoded_brand = urllib.parse.quote(brand)
    url = 'https://www.google.co.jp/search?q=' + \
        encoded_brand + '+logo&tbas=0&tbm=isch&tbs=isz:lt,islt'
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    results = soup.find_all("div", {"class": "rg_meta"})
    chosen = None
    last_diff = 1
    accept_type = ['jpg', 'jpeg', 'png']
    for result in results[0:10]:
        content = json.loads(result.text)
        if not content['ity'].lower() in accept_type:
            continue
        width = content['ow']
        height = content['oh']
        ratio = height / width if width > height else width / height
        diff = 1 - ratio
        # if content['ity'] == 'png':
        #     diff -= 0.2
        if diff < last_diff:
            chosen = content
            last_diff = diff
    extension = chosen['ity'] if chosen['ity'] else "png"
    image_file = directory + "/" + brand + "." + extension
    png_image_file = directory + "/" + brand + ".png"
    print("URL: " + chosen['ou'])
    try:
        response = requests.get(chosen['ou'], headers=headers)
    except Exception as connectionException:
        print(connectionException)
        print(" >> Google image fails")
        return
    if response.status_code == 200:
        with open(image_file, 'wb') as f:
            f.write(response.content)
    else:
        print(" >> Google image fails")
        output.write(" >> Google image fails")
        return
    resize(brand + "." + extension, directory, directory)


if __name__ == '__main__':
    main()
