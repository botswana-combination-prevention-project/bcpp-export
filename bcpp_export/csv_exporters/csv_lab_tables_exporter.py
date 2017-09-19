from edc_pdutils.csv_exporters import CsvCrfTablesExporter


class CsvLabTablesExporter(CsvCrfTablesExporter):
    """
    Example Usage:
        $ ssh -f django@bhp066.bhp.org.bw -L5002:localhost:3306 -N

        >>>
        from bcpp_export.csv_exporters import CsvLabTablesExporter
        exporter = CsvLabTablesExporter()
        exporter.to_csv()
    """
    app_label = 'bcpp_lab'
    exclude_history_tables = True
    visit_column = 'subject_visit_id'
