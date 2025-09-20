import logging

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, on_new_file_callback, logger=None):
        super().__init__()
        self.on_new_file_callback = on_new_file_callback
        self.logger = logger or logging.getLogger(__name__)

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            self.logger.info(f"Detected new file: {event.src_path}")
            self.on_new_file_callback(event.src_path)

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            self.logger.info(f"Detected modified file: {event.src_path}")
            self.on_new_file_callback(event.src_path)


class FileWatcher:
    def __init__(self, watch_dir, on_new_file_callback, logger=None):
        self.watch_dir = watch_dir
        self.logger = logger or logging.getLogger(__name__)
        self.event_handler = NewFileHandler(on_new_file_callback, self.logger)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=False)
        self.observer.start()
        self.logger.info(f"Started watching directory: {self.watch_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        self.logger.info(f"Stopped watching directory: {self.watch_dir}")
