from PIL import Image
import argparse


def convert(num_sub_images, rows, columns, filename):
    # Load the image
    image_path = filename.strip() + ".png"
    image = Image.open(image_path)

    # Get the dimensions of the image
    width, height = image.size
    # Calculate the width of each slice
    slice_width = (width // num_sub_images) * columns

    # Create a blank image to hold the stacked slices
    stacked_image_height = height * rows
    stacked_image = Image.new("RGB", (slice_width, stacked_image_height))

    # Slice the image and stack the slices on top of each other
    for i in range(rows):
        # Define the slice box (left, upper, right, lower)
        left = i * slice_width
        right = (i + 1) * slice_width
        box = (left, 0, right, height)

        # Crop the slice
        slice_img = image.crop(box)

        # Paste the slice into the stacked image at the correct position
        stacked_image.paste(slice_img, (0, stacked_image_height - (i + 1) * height))

    # Save the result
    stacked_image.save(filename + "_qs" + str(columns) + "x" + str(rows) + ".png")

    # Show the result (optional)
    #stacked_image.show()


def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Integral Image to quilt script")
    parser.add_argument("--rows", type=int, default=9)
    parser.add_argument("--columns", type=int, default=9)
    parser.add_argument("--directional_resolution", type=int, default=81)
    parser.add_argument("--filename", type=str, default="converted_quilt")

    args = parser.parse_args()
    print(args.rows, "\t", args.columns)
    convert(args.directional_resolution, args.rows, args.columns, args.filename)


if __name__ == "__main__":
    main()
