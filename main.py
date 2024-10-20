import sys
import ffmpeg
import datetime
import os

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog
)
from qt_menu import Ui_MainWindow


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, start_time, end_time, input_file, output_file, bitrate):
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time
        self.input_file = input_file
        self.output_file = output_file
        self.bitrate = bitrate

    def run(self):

        ffmpeg_path = os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe')

        self.progress.emit(50)
        # Wykonanie przycinania

        (ffmpeg
            .input(self.input_file, ss=self.start_time, to=self.end_time)
            .output(self.output_file, **{'b:v': self.bitrate}, threads=4, c='copy')
            .run(cmd=[ffmpeg_path]))

        self.progress.emit(100)
        self.finished.emit()

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicksCount = 0
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.but_wgrajPlik.clicked.connect(self.getFileName)
        
    def getFileName(self):
        self.link_str = ''
        self.link_str, _ = QFileDialog.getOpenFileName(self, 'Open file','./',"Video files (*.mp4)") 
        self.ui.lab_nazwaPliku.setText(self.link_str.split('/')[-1])

        self.getFileMetadata()

    def getFileMetadata(self):
        probe = ffmpeg.probe(self.link_str)

        self.videoMetadata = {
            'duration': str(datetime.timedelta(seconds=float(probe['format']['duration']))).split(':'),
            'bit_rate': probe['format']['bit_rate']
        }

        temp_metadata = ''
        for i, v in enumerate(probe['format'].items()):
             temp_metadata +=f'{v[0]}:{v[1]}\n'
        #     temp_metadata += f'{v}:{probe[v]}'

        self.ui.lab_dane_pliku.setText(temp_metadata)
        self.ui.lab_dane_pliku.setWordWrap(True)

        self.ui.inp_start_h.setPlainText('00')
        self.ui.inp_start_min.setPlainText('00')
        self.ui.inp_start_s.setPlainText('00')

        self.ui.inp_start_h_2.setPlainText(self.videoMetadata['duration'][0])
        self.ui.inp_start_min_2.setPlainText(self.videoMetadata['duration'][1])
        self.ui.inp_start_s_2 .setPlainText(self.videoMetadata['duration'][2])

        new_name_list = self.link_str.split('.')
        new_name_list[-2] = new_name_list[-2]+'_trim'

        self.output_fileName = ('.').join(new_name_list)
        print(self.output_fileName)
        self.ui.inp_nameOutpFile.setText(self.output_fileName.split('/')[-1])

        self.ui.but_start.clicked.connect(self.runLongTask)

    def runLongTask(self):
    
        self.thread = QThread() # Step 2: Create a QThread object
        self.worker = Worker(
            self.ui.inp_start_h.toPlainText()+':'+self.ui.inp_start_min.toPlainText()+':'+self.ui.inp_start_s.toPlainText(),
            self.ui.inp_start_h_2.toPlainText()+':'+self.ui.inp_start_min_2.toPlainText()+':'+self.ui.inp_start_s_2.toPlainText(),
            self.link_str,
            self.output_fileName,
            self.videoMetadata['bit_rate']

            )    # Step 3: Create a worker object
        self.worker.moveToThread(self.thread)   # Step 4: Move worker to the thread
        self.thread.started.connect(self.worker.run)# Step 5: Connect signals and slots
        self.worker.finished.connect(self.thread.quit)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()# Step 6: Start the thread

    def update_progress(self,e):
        self.ui.progBar_trim.setValue(int(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = Window()
    mainWindow.show()
    sys.exit(app.exec_())
