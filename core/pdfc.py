
import os
import time
import logging
from wand.image import Image


class Path:
    def __init__(self):
        self.path = None
        self.log = None

        # Initialize a logger
        LOG_FORMAT = "%(asctime)s.%(msecs)03d: [%(levelname)s] :: ( %(name)s ) :: %(message)s"
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        logging.basicConfig(filename="pdfcu_log.txt",
                            filemode='w',
                            level=logging.INFO,
                            format=LOG_FORMAT,
                            datefmt=DATE_FORMAT)
        self.log = logging.getLogger(name=self.__class__.__name__)


class Folder(Path):
    def __init__(self, directory):
        super(Folder, self).__init__()
        self.foldername = None

        try:
            # Check if provided argument is an existing directory
            if not os.path.isdir(directory):
                os.makedirs(directory)
                self.path = os.path.abspath(directory)
                self.log.info('Folder created: {}'.format(self.path))
            else:
                # Folder already exist, take the absolute path
                self.path = os.path.abspath(directory)
                self.log.info('Folder already exist: {}'.format(self.path))
            
            if self.path:
                self.foldername = self.path.split('\\')[-1]

        except TypeError:
            self.log.error('Failed to create folder', exc_info=True)

    def add_subfolder(self, folder):
        sub = Folder(os.path.join(self.path, folder))
        return sub.path

    def add_subfolders(self, folders: list):
        sub = Folder(os.path.join(self.path, *folders))
        return sub.path


class File(Path):
    def __init__(self, filepath):
        super(File, self).__init__()

        self.filename = None
        self.extension = None
        self.exists = False

        # Check if the provided argument is an existing file
        if os.path.isfile(filepath):
            self.exists = True
            self.path = os.path.abspath(filepath)
            self.filename = str(self.path.split('\\')[-1])
            self.extension = self.filename.split('.')[-1]
            self.log.info('File exist: {}'.format(filepath))
        else:
            e = 'Invalid FILEPATH: {}'.format(filepath)
            self.log.error(e)
            print(e)


class ImageFile(File):
    def __init__(self, img):
        super(ImageFile, self).__init__(img)

        self.size = None
        self.width = None
        self.height = None
        self.format = None
        self.resolution = None
        self.orientation = None
        self.read_time = None
        self.write_time = None

        if self.exists:

            with Image(filename=self.path) as wimg:
                self.size = wimg.size
                self.resolution = wimg.resolution
                self.width = wimg.width
                self.height = wimg.height
                self.format = wimg.format

            # store orientation
            if self.width > self.height:
                self.orientation = 'landscape'
            else:
                self.orientation = 'portrait'


class PdfFile(File):
    def __init__(self, pdf):
        super(PdfFile, self).__init__(pdf)

        self.page_count = None
        self.page_list = None
        self.read_time = None
        self.write_time = None
        self.date = None
        self.valid = False

        if self.extension.lower() != 'pdf':
            self.path = None
            self.filename = None
            self.extension = None
        else:
            # Make the file valid
            self.valid = True

    def read_pdf(self, res):
        timer = Timer('PDF Reading')

        # Start read timer
        timer.start_timer()

        # Read the PDF file
        with Image(filename=self.path, resolution=res) as wimg:
            self.page_list = []
            # Store pages
            for i in wimg.sequence:
                self.page_list.append(i)

        # Stop read timer
        timer.stop_timer()

        # Store page count
        self.page_count = len(self.page_list)

        # Store read time
        self.read_time = timer.get_elapsed()

    def conversion_time(self):
        timer = Timer(str('PDF Conversion [{}]').format(self.filename))

        if self.write_time is not None:

            convert_time = self.read_time + self.write_time

            name = timer.name()
            time_f = timer.format_time(convert_time)

            print('{} Elapsed Time : [{:.3f}s] -- [read: {:.3f}s / write: {:.3f}s]'.format(name, convert_time, self.read_time, self.write_time))

            return convert_time

        else:
            # print('Skipped Conversion!')
            return None


class Task:
    def __init__(self, *path: Path):

        self._inputs = list(path)

    def raw_inputs(self):
        return self._inputs


class Session:
    def __init__(self):

        self.type = None


class Timer:
    def __init__(self, name=None):
        self._start_time = None
        self._end_time = None
        self._elapsed = None
        self._name = name

    def name(self):
        return self._name

    def start_timer(self):
        self._start_time = time.time()

    def stop_timer(self):
        self._end_time = time.time()

    def format_time(self, t):
        # return time.strftime('%H:%M:%S', time.gmtime(t))
        from datetime import datetime as dt
        return dt.fromtimestamp(t).strftime('%H:%M:%S.%f')

    def get_elapsed(self, format_time=False):
        self._elapsed = self._end_time - self._start_time

        if not format_time:
            return self._elapsed
        else:
            return self.format_time(self._elapsed)

    def get_date_time(self):
        from datetime import datetime as dt
        return dt.now().strftime("%Y-%m-%d %H:%M")

    def get_date(self):
        from datetime import datetime as dt
        return dt.now().strftime("%Y-%m-%d")
