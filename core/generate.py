
# *************************************************************************************

# MODULE NAME: generate.py

# SYS-REQ: PDFC-SYS-XXX

# SW-REQ: PDFC-SRS-XXX

# MODULE DESCRIPTION: This module ...
#                     ...
#                     ...

# REVISION HISTORY:
#   $Id: generate.py 996 2018-01-09 04:39:08Z medasco $
#   PCR# N/A  Mel Dasco
#   Initial Development

# *************************************************************************************


from pdfcu.pdfc import Task, ImageFile, PdfFile, Folder, Timer
from wand.image import Image
from wand.color import Color
import cv2
import imutils
import os


class GenerateConvertTask(Task):

    def __init__(self, output_folder):

        super(GenerateConvertTask, self).__init__(output_folder)

        self.folder = Folder(output_folder)
        self.image_files = None

    def generate_image(self, subj, img_form='JPG', group=None, pages=list()):

        try:

            if img_form == 'JPG' or img_form == 'JPEG':
                img_ext = '.jpg'

            elif img_form == 'PNG':
                img_ext = '.png'

            elif img_form == 'BMP':
                img_ext = '.bmp'

            elif img_form == 'SVG':
                img_ext = '.svg'

            else:
                raise NameError('File format not supported!')

            if subj.valid:
                if pages:

                    if pages[0] == 'ALL':
                        self.image_files = self.generate_page_images_all(group, subj, img_ext)
                    else:
                        self.image_files = self.generate_page_images_sel(group, subj, img_ext, pages)

                else:
                    self.image_files = self.generate_page_images_all(group, subj, img_ext)

        except AttributeError as e:
            print(e)
        except TypeError as e:
            print(e)
        except NameError as e:
            print(e)

    @staticmethod
    def assemble_genfilename(filename, page, ext):
        return filename.rsplit('.', 1)[0] + '__pg_' + '{:02d}'.format(page) + ext

    def generate_page_images_all(self, out_folder, subj: PdfFile, img_ext):

        timer = Timer('Image Write Timer')

        # Default
        # ext = str('.' + subj.extension)
        # img_name = str(subj.filename).replace(ext, img_ext)
        # output = os.path.join(out_folder, img_name)

        img_list = []

        timer.start_timer()

        for i in range(subj.page_count):
            # Extract filename then replace extension
            img_name = self.assemble_genfilename(subj.filename, i+1, img_ext)

            # Create path where to write/save JPG files
            output = os.path.join(out_folder, img_name)

            # Write/Save JPG
            image = Image(subj.page_list[i])
            image.background_color = Color("white")
            image.alpha_channel = 'remove'
            image.save(filename=output)

            img = ImageFile(output)

            # add the image to the list
            img_list.append(img)

        timer.stop_timer()

        subj.date = timer.get_date_time()

        # store the write elapsed time
        subj.write_time = timer.get_elapsed()

        return img_list

    def generate_page_images_sel(self, out_folder, subj: PdfFile, img_ext, pg_list):
        timer = Timer('Image Write Timer')

        img_list = []

        timer.start_timer()

        for i in pg_list:
            # Extract filename then replace extension
            img_name = self.assemble_genfilename(subj.filename, i, img_ext)

            # Create path where to write/save JPG files
            output = os.path.join(out_folder, img_name)

            # Check if the file already exist
            if os.path.isfile(output):
                print('Skipped (file already exist): {}'.format(img_name))
            else:
                # Write/Save JPG
                print('Generating converted image: {}'.format(img_name))
                image = Image(subj.page_list[i-1])
                image.background_color = Color("white")
                image.alpha_channel = 'remove'
                image.save(filename=output)

            # take image information
            img = ImageFile(output)

            # add the image to the list
            img_list.append(img)

        timer.stop_timer()

        subj.date = timer.get_date_time()

        # store the write elapsed time
        subj.write_time = timer.get_elapsed()

        return img_list


class GenerateCompareTask(Task):

    def __init__(self, session_folder):

        super(GenerateCompareTask, self).__init__(session_folder)

    @staticmethod
    def generate_diff(diff, out_path):

        diff_img = (diff * 255).astype('uint8')
        cv2.imwrite(out_path, diff_img)
        return diff_img

    @staticmethod
    def generate_thres(diff, out_path):

        thres_img = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        cv2.imwrite(out_path, thres_img)
        return thres_img

    @staticmethod
    def generate_marks(thres, alpha_a, alpha_b, out_path: []):

        # Find contours to obtain the regions of the two input images that differ
        contours = cv2.findContours(thres.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if imutils.is_cv2() else contours[1]

        # Loop over the contours
        for contour in contours:
            # Compute the bounding box of the contour
            (x, y, w, h) = cv2.boundingRect(contour)
            # Draw the bounding box on both input alpha images, this represents where the two images differ
            cv2.rectangle(alpha_a, (x, y), (x + w, y + h), (255, 128, 0, 255), 5)
            cv2.rectangle(alpha_b, (x, y), (x + w, y + h), (0, 128, 255, 255), 5)

        cv2.imwrite(out_path[0], alpha_a)
        cv2.imwrite(out_path[1], alpha_b)
