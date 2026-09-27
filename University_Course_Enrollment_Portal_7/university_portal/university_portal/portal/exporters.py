import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, QuerySet

from portal.models import Classroom, Course, Department, Instructor, Section, Student, Takes

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')
EXPORT_FORMATS = ('csv', 'json')


class ExportError(ValueError):
    pass


@dataclass(frozen=True)
class Column:
    key: str
    header: str
    accessor: str

    def value(self, obj: Model) -> Any:
        current: Any = obj
        for part in self.accessor.split('__'):
            if current is None:
                return None
            current = getattr(current, part)
        return current


@dataclass(frozen=True)
class FilterSpec:
    lookup: str
    cast: Callable[[str], Any] = str


@dataclass(frozen=True)
class Dataset:
    name: str
    model: type
    columns: Tuple[Column, ...]
    filters: Dict[str, FilterSpec] = field(default_factory=dict)
    ordering: Tuple[str, ...] = ()
    select_related: Tuple[str, ...] = ()

    def column_map(self) -> Dict[str, Column]:
        return {column.key: column for column in self.columns}


def _int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ExportError(f"Expected an integer, got {value!r}")


DATASETS: Dict[str, Dataset] = {
    'students': Dataset(
        name='students',
        model=Student,
        columns=(
            Column('id', 'Student ID', 'ID'),
            Column('name', 'Name', 'name'),
            Column('department', 'Department', 'dept_name_id'),
            Column('total_credits', 'Total Credits', 'tot_cred'),
        ),
        filters={
            'department': FilterSpec('dept_name_id'),
            'name': FilterSpec('name__icontains'),
            'min_credits': FilterSpec('tot_cred__gte', _int),
            'max_credits': FilterSpec('tot_cred__lte', _int),
        },
        ordering=('ID',),
    ),
    'instructors': Dataset(
        name='instructors',
        model=Instructor,
        columns=(
            Column('id', 'Instructor ID', 'ID'),
            Column('name', 'Name', 'name'),
            Column('department', 'Department', 'dept_name_id'),
            Column('salary', 'Salary', 'salary'),
        ),
        filters={
            'department': FilterSpec('dept_name_id'),
            'name': FilterSpec('name__icontains'),
            'min_salary': FilterSpec('salary__gte', _int),
            'max_salary': FilterSpec('salary__lte', _int),
        },
        ordering=('ID',),
    ),
    'courses': Dataset(
        name='courses',
        model=Course,
        columns=(
            Column('course_id', 'Course ID', 'course_id'),
            Column('title', 'Title', 'title'),
            Column('department', 'Department', 'dept_name_id'),
            Column('credits', 'Credits', 'credits'),
        ),
        filters={
            'department': FilterSpec('dept_name_id'),
            'title': FilterSpec('title__icontains'),
            'credits': FilterSpec('credits', _int),
        },
        ordering=('course_id',),
    ),
    'departments': Dataset(
        name='departments',
        model=Department,
        columns=(
            Column('department', 'Department', 'dept_name'),
            Column('building', 'Building', 'building'),
            Column('budget', 'Budget', 'budget'),
        ),
        filters={
            'building': FilterSpec('building'),
            'min_budget': FilterSpec('budget__gte', _int),
            'max_budget': FilterSpec('budget__lte', _int),
        },
        ordering=('dept_name',),
    ),
    'classrooms': Dataset(
        name='classrooms',
        model=Classroom,
        columns=(
            Column('building', 'Building', 'building'),
            Column('room_no', 'Room No', 'room_no'),
            Column('capacity', 'Capacity', 'capacity'),
        ),
        filters={
            'building': FilterSpec('building'),
            'min_capacity': FilterSpec('capacity__gte', _int),
        },
        ordering=('building', 'room_no'),
    ),
    'sections': Dataset(
        name='sections',
        model=Section,
        columns=(
            Column('course_id', 'Course ID', 'course_id_id'),
            Column('course_title', 'Course Title', 'course_id__title'),
            Column('section', 'Section', 'sec_id'),
            Column('semester', 'Semester', 'semester'),
            Column('year', 'Year', 'year'),
            Column('building', 'Building', 'building'),
            Column('room_no', 'Room No', 'room_no'),
            Column('time_slot', 'Time Slot', 'time_slot_id'),
        ),
        filters={
            'course_id': FilterSpec('course_id_id'),
            'semester': FilterSpec('semester'),
            'year': FilterSpec('year', _int),
            'building': FilterSpec('building'),
        },
        ordering=('course_id_id', 'year', 'semester', 'sec_id'),
        select_related=('course_id',),
    ),
    'enrollments': Dataset(
        name='enrollments',
        model=Takes,
        columns=(
            Column('student_id', 'Student ID', 'ID_id'),
            Column('student_name', 'Student Name', 'ID__name'),
            Column('course_id', 'Course ID', 'course_id'),
            Column('section', 'Section', 'sec_id'),
            Column('semester', 'Semester', 'semester'),
            Column('year', 'Year', 'year'),
            Column('grade', 'Grade', 'grade'),
        ),
        filters={
            'student_id': FilterSpec('ID_id', _int),
            'course_id': FilterSpec('course_id'),
            'semester': FilterSpec('semester'),
            'year': FilterSpec('year', _int),
            'grade': FilterSpec('grade'),
            'department': FilterSpec('ID__dept_name_id'),
        },
        ordering=('ID_id', 'year', 'semester', 'course_id'),
        select_related=('ID',),
    ),
}

DATASET_BY_MODEL = {dataset.model: dataset for dataset in DATASETS.values()}


def get_dataset(name: str) -> Dataset:
    try:
        return DATASETS[name]
    except KeyError:
        raise ExportError(f"Unknown dataset {name!r}. Choose from: {', '.join(sorted(DATASETS))}")


def select_columns(dataset: Dataset, keys: Optional[Sequence[str]] = None) -> List[Column]:
    if not keys:
        return list(dataset.columns)
    available = dataset.column_map()
    unknown = [key for key in keys if key not in available]
    if unknown:
        raise ExportError(
            f"Unknown column(s) for {dataset.name}: {', '.join(unknown)}. "
            f"Choose from: {', '.join(available)}"
        )
    return [available[key] for key in dict.fromkeys(keys)]


def build_queryset(dataset: Dataset, filters: Optional[Dict[str, str]] = None,
                   queryset: Optional[QuerySet] = None) -> Tuple[QuerySet, Dict[str, Any]]:
    queryset = dataset.model.objects.all() if queryset is None else queryset
    applied: Dict[str, Any] = {}
    for key, raw in (filters or {}).items():
        if raw is None or str(raw).strip() == '':
            continue
        spec = dataset.filters.get(key)
        if spec is None:
            raise ExportError(
                f"Unsupported filter {key!r} for {dataset.name}. "
                f"Choose from: {', '.join(sorted(dataset.filters)) or 'none'}"
            )
        value = spec.cast(str(raw).strip())
        applied[key] = value
        queryset = queryset.filter(**{spec.lookup: value})
    if dataset.select_related:
        queryset = queryset.select_related(*dataset.select_related)
    if dataset.ordering:
        queryset = queryset.order_by(*dataset.ordering)
    try:
        queryset.exists()
    except (ValueError, ValidationError) as exc:
        raise ExportError(f"Invalid filter value: {exc}")
    return queryset, applied


def sanitize_cell(value: Any) -> Any:
    if value is None:
        return ''
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


class _Echo:
    def write(self, value: str) -> str:
        return value


def iter_csv(rows: Iterable[Model], columns: Sequence[Column], include_header: bool = True) -> Iterator[str]:
    writer = csv.writer(_Echo())
    if include_header:
        yield writer.writerow([column.header for column in columns])
    for obj in rows:
        yield writer.writerow([sanitize_cell(column.value(obj)) for column in columns])


def export_metadata(dataset: Dataset, columns: Sequence[Column], filters: Dict[str, Any],
                    count: int) -> Dict[str, Any]:
    return {
        'dataset': dataset.name,
        'generated_at': datetime.now(dt_timezone.utc).isoformat(timespec='seconds'),
        'filters': filters,
        'count': count,
        'columns': [{'key': column.key, 'header': column.header} for column in columns],
    }


def iter_json(rows: QuerySet, dataset: Dataset, columns: Sequence[Column],
              filters: Dict[str, Any]) -> Iterator[str]:
    meta = export_metadata(dataset, columns, filters, rows.count())
    encoder = DjangoJSONEncoder()
    head = json.dumps(meta, cls=DjangoJSONEncoder)[:-1]
    yield head + ', "records": ['
    for index, obj in enumerate(rows.iterator(chunk_size=500)):
        record = {column.key: column.value(obj) for column in columns}
        yield (', ' if index else '') + encoder.encode(record)
    yield ']}'


def export_filename(dataset: Dataset, fmt: str) -> str:
    stamp = datetime.now(dt_timezone.utc).strftime('%Y%m%d-%H%M%S')
    return f"{dataset.name}-{stamp}.{fmt}"
