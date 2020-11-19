
# *************************************************************************************

# MODULE NAME: report.py

# SYS-REQ: PDFC-SYS-XXX

# SW-REQ: PDFC-SRS-XXX

# MODULE DESCRIPTION: This module ...
#                     ...
#                     ...

# REVISION HISTORY:
#   $Id: report.py 1110 2018-02-13 06:01:23Z mdasco $
#   PCR# N/A  Mel Dasco
#   Initial Development

# *************************************************************************************


from pdfcu.pdfc import Folder, Task, PdfFile, ImageFile, Timer
import pandas as pd
from xlsxwriter import Workbook
import os


class ReportTask(Task):

    def __init__(self, report_folder):
        super(ReportTask, self).__init__(report_folder)

        self.folder = Folder(report_folder)
        self.file = None


class PdfConversionReporter(ReportTask):
    def __init__(self, report_dir, source: PdfFile, image_list: [ImageFile]):
        super(PdfConversionReporter, self).__init__(report_dir)

        self.source = source
        self.image_pages = image_list

        # create data frame object
        self.df = pd.DataFrame(columns=None)

        self.file = os.path.join(report_dir, '_conversion.report')

    def create_report(self):

        # Look for pre-existing report file
        if not os.path.isfile(self.file):
            # add a new report
            self.add_report()
        else:
            # remove existing report
            self.remove_report()

            # create a new report
            self.add_report()

        # gather information
        image_info_list = []

        for img in self.image_pages:
            source = self.source.filename
            page = int(img.filename.split(str(img.format).lower())[0].split('.')[0].split('_')[-1])
            filename = img.filename

            fmt = img.format
            res = img.resolution[0]
            orient = img.orientation
            width = img.width
            height = img.height

            tpage = self.source.page_count
            date = self.source.date
            fpath = img.path
            srcpath = self.source.path

            element = [source,
                       page,
                       filename,
                       fmt,
                       res,
                       orient,
                       width,
                       height,
                       tpage,
                       date,
                       fpath,
                       srcpath]

            image_info_list.append(element)

        # create data frame
        cols = ['source',
                'page',
                'filename',
                'format',
                'resolution',
                'orientation',
                'width',
                'height',
                'totalpage',
                'date',
                'fpath',
                'srcpath']

        self.df = pd.DataFrame(image_info_list, columns=cols)

        # save report
        with open(self.file, 'a') as f:
            self.df.to_csv(f, index=False)

    def add_report(self):
        # create a new report file
        f = open(self.file, 'a')
        f.write('#')
        f.write('*' * 120)
        f.write('\n#')
        f.write('\n# source       : {}'.format(self.source.filename))
        f.write('\n# source path  : {}'.format(self.source.path))
        f.write('\n# page count   : {} pages'.format(self.source.page_count))
        f.write('\n# date         : {}'.format(self.source.date))
        f.write('\n# convert time : {:.3f}s -- '.format(self.source.read_time + self.source.write_time))
        f.write('[read: {:.3f}s | write: {:.3f}s]'.format(self.source.read_time, self.source.write_time))
        f.write('\n#')
        f.write('\n#')
        f.write('*' * 120)
        f.write('\n\n\n')

        # initialize the file data
        self.df.to_csv(f, header=None)

        # close the file
        f.close()

    def remove_report(self):
        os.remove(self.file)


class ImageComparisonReporter(ReportTask):
    def __init__(self, report_dir, compare_task):

        self.compare_task = compare_task

        super(ImageComparisonReporter, self).__init__(report_dir)

        self.columns = ['source_a',
                        'page_a',
                        'source_b',
                        'page_b',
                        'score',
                        'ctype',
                        'valid',
                        'name',
                        'duration',
                        'date',
                        'image_a_path',
                        'image_b_path',
                        'diff_path',
                        'thres_path',
                        'marks_a_path',
                        'marks_b_path']

        self.df = pd.DataFrame(columns=self.columns)

        self.file = os.path.join(report_dir, '_comparison.report')

    def create_report(self):
        # Look for pre-existing report file
        if not os.path.isfile(self.file):
            # add a new report
            f = open(self.file, 'a')

            # initialize the file data
            self.df.to_csv(f, index=None)

            # close the file
            f.close()

        else:
            # read the report
            self.df = pd.read_csv(self.file)

            self.df['score'] = self.df['score'].map('{:.05f}'.format)
            self.df['duration'] = self.df['duration'].map('{:.05f}'.format)

        # create new info data
        src_a = self.compare_task.source_a
        pg_a = self.compare_task.source_a_pg
        src_b = self.compare_task.source_b
        pg_b = self.compare_task.source_b_pg

        valid = self.compare_task.isvalid
        score = str('{:.05f}').format(self.compare_task.score)
        ctype = self.compare_task.type

        name = self.compare_task.name
        duration = str('{:.05f}').format(self.compare_task.time)
        date = self.compare_task.date

        img_a_path = self.compare_task.file_a.path
        img_b_path = self.compare_task.file_b.path

        diff_path = self.compare_task.diffpath()
        thres_path = self.compare_task.threspath()
        marks = self.compare_task.markspath()
        marks_a_path = marks[0]
        marks_b_path = marks[1]

        new_data = [src_a,
                    pg_a,
                    src_b,
                    pg_b,
                    score,
                    ctype,
                    valid,
                    name,
                    duration,
                    date,
                    img_a_path,
                    img_b_path,
                    diff_path,
                    thres_path,
                    marks_a_path,
                    marks_b_path]

        new_df = pd.DataFrame([new_data], columns=self.columns)

        # append new report
        self.df = pd.DataFrame(pd.concat([self.df, new_df], ignore_index=True))

        # save report
        self.df.to_csv(self.file, index=None)


class ReportGleaner(ReportTask):

    def __init__(self, report_name, src_folder, dest_folder):
        super(ReportGleaner, self).__init__(src_folder)

        Folder(dest_folder)
        self.file = os.path.abspath(os.path.join(dest_folder, '{}__{}.xlsx'.format(report_name, Timer().get_date())))

        self.conv_df = pd.DataFrame()
        self.comp_df = pd.DataFrame()

        self.writer = None
        self.workbook = None

    def scan_conversions(self, folder):

        result = []
        for root, dirs, files in os.walk(folder):
            for name in files:
                if name == '_conversion.report':
                    result.append(os.path.join(root, name))

        for p in result:
            df = pd.read_csv(p, comment='#')
            self.conv_df = pd.DataFrame(pd.concat([self.conv_df, df], ignore_index=True))

        # self.conv_df.to_csv(os.path.join(self.folder.path, '_all_conversions.report'), index=False)

    def scan_comparisons(self, folder):

        result = []
        for root, dirs, files in os.walk(folder):
            for name in files:
                if name == '_comparison.report':
                    result.append(os.path.join(root, name))

        for p in result:
            df = pd.read_csv(p)
            self.comp_df = pd.DataFrame(pd.concat([self.comp_df, df], ignore_index=True))

        # self.comp_df.to_csv(os.path.join(self.folder.path, '_all_comparisons.report'), index=False)

    def scan_reports(self):
        self.scan_conversions(self.folder.path)
        self.scan_comparisons(self.folder.path)

    def gather_reports(self):

        def_fmt_prop = {'font': 'Consolas', 'font_size': 9, 'align': 'center', 'valign': 'center'}
        self.workbook = Workbook(self.file, options={'default_format_properties': def_fmt_prop})

        # formats
        rawhead_fmt = self.workbook.add_format({'bold': True, 'align': 'center', 'valign': 'center'})

        # worksheets
        convert_ws = self.workbook.add_worksheet('_convert_raw')
        compare_ws = self.workbook.add_worksheet('_compare_raw')

        # headers for raw data sheets
        convert_ws.write_row(0, 0, list(self.conv_df), rawhead_fmt)
        compare_ws.write_row(0, 0, list(self.comp_df), rawhead_fmt)

        # add auto filter on headers
        convert_ws.autofilter(0, 0, 0, len(self.conv_df.columns) - 1)
        compare_ws.autofilter(0, 0, 0, len(self.comp_df.columns) - 1)

        # populate raw data sheets
        for i in range(len(self.conv_df)):
            convert_ws.write_row('A{}'.format(i+2), self.conv_df.iloc[i])

        for i in range(len(self.comp_df)):
            compare_ws.write_row('A{}'.format(i+2), self.comp_df.iloc[i])

    def summary_report(self):

        summary_ws = self.workbook.add_worksheet('summary')

        # formats
        head_fmt = self.workbook.add_format({'bold': True, 'align': 'center', 'valign': 'center'})
        percent_fmt = self.workbook.add_format({'num_format': '0.00 %'})

        # populate the summary sheet
        df = self.comp_df[['source_a', 'page_a', 'source_b', 'page_b', 'score', 'ctype', 'valid', 'name']]

        # headers for summary sheet
        summary_ws.write_row(0, 0, list(df), head_fmt)

        # populate summary sheet
        for i in range(len(df)):
            summary_ws.write_row('A{}'.format(i + 2), df.iloc[i])

        # set number format
        summary_ws.set_column(4, 4, cell_format=percent_fmt)

        # add auto filter on headers
        summary_ws.autofilter(0, 0, 0, len(df.columns) - 1)

        # arrange the worksheets
        sheetlist = ['summary', '_convert_raw', '_compare_raw']
        self.workbook.worksheets_objs.sort(key=lambda x: sheetlist.index(x.name))

        sheet_count = len(self.workbook.worksheets_objs)

        # close workbook
        self.workbook.close()

        # autofit columns
        self.autofit_columns(sheet_count)

    def autofit_columns(self, sheet_count):

        from win32com.client import Dispatch

        excel = Dispatch('Excel.Application')
        wb = excel.Workbooks.Open(self.file)

        # activate second sheet
        for i in range(sheet_count):
            excel.Worksheets(i+1).Activate()

            # autofit column in active sheet
            excel.ActiveSheet.Columns.AutoFit()

        # activate the first sheet
        excel.Worksheets(1).Activate()

        # save changes in a current file
        wb.Save()

        wb.Close()

    def create_report(self):

        # scan existing report files
        self.scan_reports()

        # gather and attach the raw data reports
        self.gather_reports()

        # summarize report
        self.summary_report()
