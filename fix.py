import os
from PIL import Image, ImageOps


def main():
    need_fix_dir = "need_fix"
    fixed_dir = "fixed"
    if not os.path.exists(fixed_dir):
        os.makedirs(fixed_dir)
    for file in os.listdir(need_fix_dir):
        fullname = os.fsdecode(file)
        if fullname[0] == ".":
            continue
        resize(fullname, need_fix_dir, fixed_dir)


def resize(fullname, input_dir, output_dir):
    size = (800, 800)
    print(f"Resizing {fullname}. ", end='')
    filename, file_extension = os.path.splitext(fullname)
    orig_path = os.path.join(input_dir, fullname)
    fixed_path = os.path.join(output_dir, fullname)
    fixed_png_path = os.path.join(output_dir, filename + ".png")
    img = Image.open(orig_path)
    height, width = img.size
    max_dim = height if height > width else width
    ratio = size[0] / max_dim
    new_height = int(ratio * height)
    new_width = int(ratio * width)
    resized_img = img.resize((new_height, new_width), Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(
        resized_img, (int((size[0] - new_height) / 2), int((size[0] - new_width) / 2)))
    # resized_img = ImageOps.fit(img1, (800, 800), Image.ANTIALIAS)
    # resized_img.thumbnail((800, 800), Image.ANTIALIAS)
    try:
        background.save(fixed_path)
    except OSError:
        print(" >> Wrong format. Try to convert to png")
        if os.path.isfile(fixed_path):
            os.remove(fixed_path)
        try:
            background.save(fixed_png_path)
        except OSError:
            print(" >> Fail to convert to png ")
            return
    print("Done!")


if __name__ == '__main__':
    main()
