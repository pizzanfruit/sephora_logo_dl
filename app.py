import requests
import urllib.request
import os
import xlrd
import PIL
from PIL import Image

COUNT = 0


def main():
    directory = "logos"
    if not os.path.exists(directory):
        os.makedirs(directory)

    wb = xlrd.open_workbook("brands.xlsx")
    wb.sheet_names()
    sh = wb.sheet_by_index(0)
    brands = sh.col_values(0)
    with open("output.txt", "w") as output:
        for brand in brands:
            saveLogo(brand, directory, output)


def saveLogo(brand, directory, output):
    output.write("\n")
    domain_endpoint = "https://company.clearbit.com/v1/domains/find?name=" + brand
    headers = {
        'Authorization': 'Bearer sk_53839e6d7fbe624d0ea5d376ef3ea02e',
    }
    r = requests.get(domain_endpoint, headers=headers).json()
    global COUNT
    COUNT = COUNT + 1
    o1 = str(COUNT) + ". " + brand
    print(o1)
    output.write(o1)
    if 'error' in r:
        print("** No domain")
        output.write("** No domain")
        return
    domain_name = r['domain']
    image_endpoint = 'https://logo.clearbit.com/' + domain_name
    print(" >> " + image_endpoint)
    output.write(" >> " + image_endpoint)
    try:
        image_file = directory + "/" + brand + ".png"
        urllib.request.urlretrieve(
            image_endpoint, image_file)
        img1 = Image.open(image_file)
        resized_img = img1.resize((500, 500), Image.ANTIALIAS)
        resized_img.save(image_file)
    except urllib.error.HTTPError:
        print(" >> No logo")
        output.write(" >> No logo")
        return


if __name__ == '__main__':
    main()
