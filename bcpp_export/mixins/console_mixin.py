import sys


class ConsoleMixin(object):
    def output_to_console(self, text):
        """Outputs a text string to the console."""
        sys.stdout.write(text)
        sys.stdout.flush()

    def progress_to_console(self, text, index, count):
        """Outputs the progress to console while staying on one line."""
        progress = round(100 * (float(index) / float(count)))
        sys.stdout.write('{0} [{1} %] \r'.format(text, progress))
        sys.stdout.flush()
