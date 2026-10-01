"""Single-process album writes and secret-free export."""
import hashlib
import json
import os
import threading
import uuid
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

_LOCK = threading.RLock()


def read_json(path):
    if not path.exists():
        return {}
    result = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(result, dict):
        raise ValueError(f'{path.name}의 최상위 값은 객체여야 합니다. 기존 파일을 확인해주세요.')
    return result


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def save_photo(base, raw, source_id, when, title, description, add_timeline):
    if not title.strip():
        raise ValueError('제목을 입력해주세요.')
    with _LOCK:
        metadata_path, timeline_path = base / 'data/pictures.json', base / 'data/timeline.json'
        metadata, timeline = read_json(metadata_path), read_json(timeline_path)
        if any(isinstance(v, dict) and v.get('source_id') == source_id for v in metadata.values()):
            return False
        year = str(when.year)
        if not isinstance(timeline.get(year, []), list):
            raise ValueError('해당 연도의 Timeline 형식을 확인해주세요.')
        digest = hashlib.sha256(source_id.encode()).hexdigest()[:24]
        relative = f'images/{year}/pictures/import_{digest}.jpg'
        image_path = base / relative
        if image_path.exists():
            raise ValueError('같은 사진 파일이 이미 있습니다. 기존 기록을 확인해주세요.')
        metadata[relative] = {'caption': title.strip() + '\n' + description.strip(),
                              'date': when.isoformat(), 'source_id': source_id}
        if add_timeline:
            timeline.setdefault(year, []).append({'date': when.isoformat(), 'title': title.strip(),
                'description': description.strip(), 'image': relative, 'source_id': source_id})
            timeline[year].sort(key=lambda e: str(e.get('date', '')) if isinstance(e, dict) else '')
        old_meta = metadata_path.read_bytes() if metadata_path.exists() else None
        old_timeline = timeline_path.read_bytes() if timeline_path.exists() else None
        try:
            atomic_write(image_path, raw)
            atomic_write(metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2).encode())
            atomic_write(timeline_path, json.dumps(timeline, ensure_ascii=False, indent=2).encode())
        except Exception:
            image_path.unlink(missing_ok=True)
            for path, old in [(metadata_path, old_meta), (timeline_path, old_timeline)]:
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, old)
            raise
        return True


def export_album(base):
    with _LOCK:
        out = BytesIO()
        with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
            files = list(base.glob('*.py')) + list(base.glob('*.md'))
            files += [base / 'requirements.txt', base / '.gitignore', base / '.streamlit/config.toml',
                      base / '.streamlit/secrets.toml.example']
            files += list((base / 'data').rglob('*.json')) + list((base / 'images').rglob('*'))
            for path in sorted(set(files)):
                if path.is_file():
                    archive.write(path, 'sennie/' + path.relative_to(base).as_posix())
        return out.getvalue()


def remove_timeline_event(base, year, event):
    """Remove one matching Timeline entry; keep Picture metadata and image files."""
    with _LOCK:
        path = base / 'data/timeline.json'
        timeline = read_json(path)
        entries = timeline.get(str(year), [])
        if not isinstance(entries, list):
            raise ValueError('Timeline 형식을 확인해주세요.')
        for index, current in enumerate(entries):
            if current == event:
                entries.pop(index)
                atomic_write(path, json.dumps(timeline, ensure_ascii=False, indent=2).encode())
                return True
        return False


def delete_picture(base, relative):
    """Delete an album Picture and remove its Timeline references; Google originals are untouched."""
    base = base.resolve()
    path = (base / relative).resolve()
    parts = Path(relative).parts
    if (not path.is_relative_to(base) or len(parts) != 4 or parts[0] != 'images'
            or not parts[1].isdigit() or parts[2] != 'pictures' or not path.is_file()):
        raise ValueError('Picture 폴더의 사진만 삭제할 수 있습니다.')
    with _LOCK:
        meta_path, timeline_path = base / 'data/pictures.json', base / 'data/timeline.json'
        metadata, timeline = read_json(meta_path), read_json(timeline_path)
        metadata.pop(relative, None)
        for year, entries in timeline.items():
            if not isinstance(entries, list):
                raise ValueError('Timeline 형식을 확인해주세요.')
            keep = []
            for event in entries:
                if not isinstance(event, dict):
                    keep.append(event)
                    continue
                event = dict(event)
                values = event.get('images')
                if isinstance(values, list) and relative in values:
                    values = [value for value in values if value != relative]
                    if not values:
                        continue
                    event['images'] = values
                    if event.get('image') == relative:
                        event['image'] = values[0]
                elif event.get('image') == relative:
                    continue
                keep.append(event)
            timeline[year] = keep
        originals = {p: p.read_bytes() if p.exists() else None for p in (meta_path, timeline_path)}
        try:
            atomic_write(meta_path, json.dumps(metadata, ensure_ascii=False, indent=2).encode())
            atomic_write(timeline_path, json.dumps(timeline, ensure_ascii=False, indent=2).encode())
            path.unlink()
        except Exception:
            for p, raw in originals.items():
                if raw is None:
                    p.unlink(missing_ok=True)
                else:
                    atomic_write(p, raw)
            raise
