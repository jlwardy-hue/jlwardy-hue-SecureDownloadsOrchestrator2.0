import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, on_new_file_callback):
        super().__init__()
        self.on_new_file_callback = on_new_file_callback

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            logging.info(f"Detected new file: {event.src_path}")
            self.on_new_file_callback(event.src_path)

class FileWatcher:
    def __init__(self, watch_dir, on_new_file_callback):
        self.watch_dir = watch_dir
        self.event_handler = NewFileHandler(on_new_file_callback)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=False)
        self.observer.start()
        logging.info(f"Started watching directory: {self.watch_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()