
# *************************************************************************************

# MODULE NAME: compare.py

# SYS-REQ: PDFC-SYS-XXX

# SW-REQ: PDFC-SRS-XXX

# MODULE DESCRIPTION: This module ...
#                     ...
#                     ...

# REVISION HISTORY:
#   $Id: compare.py 776 2017-11-06 07:31:03Z medasco $
#   PCR# N/A  Mel Dasco
#   Initial Development

# *************************************************************************************


from pdfcu.pdfc import ImageFile, Task, Folder, Timer
from pdfcu.generate import GenerateCompareTask
from pdfcu.report import ImageComparisonReporter
from pdfcu.util.ssim import compare_ssim
from numpy import zeros
import cv2
import os


class ImageCompareTask(Task):
    def __init__(self, session_folder, report=False, typ='manual'):

        super(ImageCompareTask, self).__init__(session_folder)

        self.folder = Folder(session_folder)
        self.source_a = None
        self.source_b = None
        self.source_a_pg = None
        self.source_b_pg = None
        self.name = None
        self.file_a = None
        self.file_b = None
        self.alpha_a = None
        self.alpha_b = None
        self.score = None
        self.diff = None
        self.thres = None
        self.marks = None
        self.generator = GenerateCompareTask(session_folder)
        self.isreporting = report
        self.isvalid = False
        self.time = None
        self.date = None
        self.type = typ

    def validate_files(self):

        if (self.file_a is not None and self.file_b is not None) and \
           (self.file_a.orientation == self.file_b.orientation) and \
           (self.file_a.size == self.file_b.size):

            self.isvalid = True

            # Read images as OpenCV
            cv_file_a = cv2.imread(self.file_a.path)
            cv_file_b = cv2.imread(self.file_b.path)

            # Generate alpha image for the markers
            aH, aW = cv_file_a.shape[:2]
            bH, bW = cv_file_b.shape[:2]
            self.alpha_a = zeros((aH, aW, 4), dtype='uint8')
            self.alpha_b = zeros((bH, bW, 4), dtype='uint8')

            # Convert to grayscale
            gray_file_a = cv2.cvtColor(cv_file_a, cv2.COLOR_BGR2GRAY)
            gray_file_b = cv2.cvtColor(cv_file_b, cv2.COLOR_BGR2GRAY)

            # Compute SSIM between two grayscale images
            (self.score, self.diff) = compare_ssim(gray_file_a, gray_file_b, full=True)

        else:
            self.isvalid = False

        self.name = self.file_a.filename.rsplit('.', 1)[0] + '_vs_' + self.file_b.filename.rsplit('.', 1)[0]

    def set_session_path(self, subfolder: [str], img_form='JPG'):

        ext = None

        if img_form == 'JPG':
            ext = '.jpg'
        elif img_form == 'PNG':
            ext = '.png'

        p = self.folder.add_subfolders(subfolder)

        return os.path.join(p, self.name + ext)

    def diffpath(self):
        return self.set_session_path(['diff'], 'JPG')

    def threspath(self):
        return self.set_session_path(['thres'], 'JPG')

    def markspath(self):
        fpath = self.set_session_path(['marks'], 'PNG')

        mrk_img_a = str(fpath).split('.')[0] + '_a.png'
        mrk_img_b = str(fpath).split('.')[0] + '_b.png'

        return [mrk_img_a, mrk_img_b]

    def read_images(self, file_a, file_b):

        self.file_a = ImageFile(file_a)
        self.file_b = ImageFile(file_b)

        self.source_a = self.file_a.filename.split('__pg_')[0]
        self.source_b = self.file_b.filename.split('__pg_')[0]

        self.source_a_pg = int(self.file_a.filename.split('__pg_')[1].split('.')[0])
        self.source_b_pg = int(self.file_b.filename.split('__pg_')[1].split('.')[0])

    def compare_images(self):

        timer = Timer()

        timer.start_timer()

        # validate images
        self.validate_files()

        if self.isvalid:

            # DIFFERENCE
            self.diff = self.generator.generate_diff(self.diff, self.diffpath())

            # THRESHOLD
            self.thres = self.generator.generate_thres(self.diff, self.threspath())

            # MARKINGS
            self.marks = self.generator.generate_marks(self.thres, self.alpha_a, self.alpha_b, self.markspath())

        print('Comparing: {} vs {} :: ssim: {:.3f} %\n'.format(self.file_a.filename,
                                                               self.file_b.filename,
                                                               'INVALID' if self.score is None else self.score * 100.0))

        timer.stop_timer()

        self.time = timer.get_elapsed()
        self.date = timer.get_date_time()

        if self.isreporting:
            reporter = ImageComparisonReporter(self.folder.path, self)
            reporter.create_report()
