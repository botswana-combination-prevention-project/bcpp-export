from edc.export.classes import ExportPlan
dct = {
    'name': 'test_plan',
    'fields': [],
    'extra_fields': {},
    'exclude': [],
    'header': True,
    'track_history': True,
    'show_all_fields': True,
    'delimiter': '|',
    'encrypt': False,
    'strip': True,
    'target_path': '~/export_to_cdc',
    'notification_plan_name': 'referral_file_to_cdc',
}

export_plan = ExportPlan(**dct)
