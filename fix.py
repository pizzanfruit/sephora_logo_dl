import os
from PIL import Image, ImageOps


def main():
    need_fix_dir = "need_fix"
    fixed_dir = "fixed"
    for file in os.listdir(need_fix_dir):
        fullname = os.fsdecode(file)
        resize(fullname, need_fix_dir, fixed_dir)

def resize(fullname, input_dir, output_dir):
    print(f"Resizing {fullname}. ", end='')
    filename, file_extension = os.path.splitext(fullname)
    orig_path = os.path.join(input_dir, fullname)
    fixed_path = os.path.join(output_dir, fullname)
    fixed_png_path = os.path.join(output_dir, filename + ".png")
    img1 = Image.open(orig_path)
    resized_img = ImageOps.fit(img1, (800, 800), Image.ANTIALIAS)
    try:
        resized_img.save(fixed_path)
    except OSError as error:
        print(" >> Wrong format. Try to convert to png")
        print(error)
        if os.path.isfile(fixed_path):
            print("why am i here")
            os.remove(fixed_path)
        try:
            resized_img.save(fixed_png_path)
        except OSError as error2:
            print(" >> Fail to convert to png ")
            print(error2)
            return
    print("Done!")


if __name__ == '__main__':
    main()
