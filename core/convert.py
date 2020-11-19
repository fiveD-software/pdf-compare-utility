
# *************************************************************************************

# MODULE NAME: convert.py

# SYS-REQ: PDFC-SYS-XXX

# SW-REQ: PDFC-SRS-XXX

# MODULE DESCRIPTION: This module ...
#                     ...
#                     ...

# REVISION HISTORY:
#   $Id: convert.py 947 2017-12-20 06:17:10Z mdasco $
#   PCR# N/A  Mel Dasco
#   Initial Development

# *************************************************************************************


from pdfcu.pdfc import PdfFile, Task
from pdfcu.generate import GenerateConvertTask
from pdfcu.report import PdfConversionReporter


class PdfConvertTask(Task):

    def __init__(self, subj_path, gen_path, report=False):

        super(PdfConvertTask, self).__init__(subj_path)

        self.subject = PdfFile(subj_path)
        self.generator = GenerateConvertTask(gen_path)
        self.group = None
        self.reporter = None
        self.isreporting = report

        # Read the PDF file under 320 resolution
        self.subject.read_pdf(res=320)

    def set_group(self, grpname=None, subfolders: list=None):
        if grpname is None:
            name = self.subject.filename.rsplit('.', 1)[0]
        else:
            name = grpname

        if subfolders:
            subfolders.append(name)
            self.group = self.generator.folder.add_subfolders(subfolders)
        else:
            self.group = self.generator.folder.add_subfolders([name])

    def pdf_to_image(self, pages: list, imgformat='JPG'):

        # check if group name is still not set (then set default)
        if self.group is None:
            self.set_group()

        # Generate JPG file from a given converted PDF file
        self.generator.generate_image(self.subject, imgformat, self.group, pages=pages)

        # Conversion elapsed time
        self.subject.conversion_time()

        # Reporting
        if self.isreporting:
            self.reporter = PdfConversionReporter(self.group, self.subject, self.generator.image_files)
            self.reporter.create_report()
