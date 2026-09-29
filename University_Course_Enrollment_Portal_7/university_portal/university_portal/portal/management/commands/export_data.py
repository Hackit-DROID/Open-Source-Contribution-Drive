from django.core.management.base import BaseCommand, CommandError

from portal.exporters import (
    DATASETS,
    EXPORT_FORMATS,
    ExportError,
    build_queryset,
    get_dataset,
    iter_csv,
    iter_json,
    select_columns,
)


class Command(BaseCommand):
    help = 'Export portal records as CSV or JSON.'

    def add_arguments(self, parser):
        parser.add_argument('dataset', choices=sorted(DATASETS))
        parser.add_argument('--format', choices=EXPORT_FORMATS, default='csv', dest='fmt')
        parser.add_argument('--output', '-o', help='File to write. Defaults to stdout.')
        parser.add_argument('--filter', action='append', default=[], dest='filters',
                            help='Filter as key=value. Can be repeated.')
        parser.add_argument('--columns', help='Comma separated column keys to include, in order.')
        parser.add_argument('--no-header', action='store_true', help='Omit the CSV header row.')

    def handle(self, *args, **options):
        filters = self._parse_filters(options['filters'])
        column_keys = [key.strip() for key in (options['columns'] or '').split(',') if key.strip()]

        try:
            dataset = get_dataset(options['dataset'])
            columns = select_columns(dataset, column_keys)
            queryset, applied = build_queryset(dataset, filters)
        except ExportError as exc:
            raise CommandError(str(exc))

        if options['fmt'] == 'csv':
            chunks = iter_csv(queryset.iterator(chunk_size=500), columns, include_header=not options['no_header'])
        else:
            chunks = iter_json(queryset, dataset, columns, applied)

        output = options['output']
        if output:
            with open(output, 'w', newline='', encoding='utf-8') as handle:
                handle.writelines(chunks)
            self.stderr.write(self.style.SUCCESS(
                f"Exported {queryset.count()} {dataset.name} record(s) to {output}."
            ))
        else:
            for chunk in chunks:
                self.stdout.write(chunk, ending='')

    def _parse_filters(self, items):
        filters = {}
        for item in items:
            key, separator, value = item.partition('=')
            if not separator or not key.strip():
                raise CommandError(f'Invalid --filter "{item}". Use key=value.')
            filters[key.strip()] = value
        return filters
