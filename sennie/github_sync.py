"""Atomic GitHub data commits, with optimistic concurrency and no force push."""
import base64
import hashlib
import json
import re
from urllib.parse import quote
import requests


class GitHubSyncError(ValueError):
    pass


def _setting(name, default=''):
    import streamlit as st
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def git_hash(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def _same(old, remote, path):
    if old == remote:
        return True
    if path.endswith('.json'):
        try:
            return json.loads((old or b'{}').decode('utf-8-sig')) == json.loads((remote or b'{}').decode('utf-8-sig'))
        except (ValueError, UnicodeError):
            pass
    return False


class GitHubSync:
    def __init__(self, token, repo, branch='', prefix='sennie'):
        if not token:
            raise GitHubSyncError('자동 저장 설정이 필요합니다. Secrets에 GITHUB_TOKEN을 입력해주세요. 변경사항은 저장하지 않았습니다.')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise GitHubSyncError('GITHUB_REPO는 empasend-poop/Sennie 형식으로 입력해주세요.')
        prefix = prefix.strip('/')
        if prefix and any(p in ('', '.', '..') for p in prefix.split('/')):
            raise GitHubSyncError('GITHUB_BASE_PATH 설정을 확인해주세요.')
        self.root = 'https://api.github.com/repos/' + repo
        self.prefix, self.branch = prefix, branch
        self.headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                        'X-GitHub-Api-Version': '2022-11-28'}

    def api(self, method, path, **kwargs):
        try:
            response = requests.request(method, self.root + path, headers=self.headers,
                                        timeout=45, allow_redirects=False, **kwargs)
        except requests.RequestException as exc:
            raise GitHubSyncError('GitHub 연결에 실패했습니다. 잠시 후 다시 시도해주세요.') from exc
        if not response.ok:
            code = response.status_code
            reason = {401: '토큰 또는 만료일', 403: 'Contents 쓰기 권한·호출 제한',
                      404: '저장소·브랜치·토큰의 저장소 접근 권한',
                      409: '동시 변경 또는 브랜치 상태', 422: '동시 변경·브랜치 보호 규칙'}.get(code, '설정·서비스 상태')
            raise GitHubSyncError(f'GitHub 반영 실패 (HTTP {code}). {reason}을 확인해주세요. 변경사항을 완료로 처리하지 않았습니다.')
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubSyncError('GitHub 응답을 확인하지 못했습니다.') from exc

    def repo_path(self, relative):
        if relative not in ('data/timeline.json', 'data/pictures.json'):
            parts = relative.split('/')
            if len(parts) != 4 or parts[0] != 'images' or not parts[1].isdigit() or parts[2] != 'pictures' or parts[3] in ('', '.', '..'):
                raise GitHubSyncError('앨범 사진·기록 파일만 자동 반영할 수 있습니다.')
        return self.prefix + '/' + relative if self.prefix else relative

    def head(self):
        if not self.branch:
            self.branch = self.api('GET', '')['default_branch']
        return self.api('GET', '/git/ref/heads/' + quote(self.branch, safe='/'))['object']['sha']

    def prepare(self, before):
        self.parent = self.head()
        self.base_tree = self.api('GET', '/git/commits/' + self.parent)['tree']['sha']
        tree = self.api('GET', '/git/trees/' + self.base_tree, params={'recursive': '1'})
        if tree.get('truncated'):
            raise GitHubSyncError('저장소 파일 목록이 너무 커 확인하지 못했습니다.')
        self.entries = {e['path']: e for e in tree['tree'] if e['type'] == 'blob'}
        for relative, old in before.items():
            path = self.repo_path(relative)
            entry = self.entries.get(path)
            if relative.endswith('.json'):
                remote = None
                if entry:
                    blob = self.api('GET', '/git/blobs/' + entry['sha'])
                    remote = base64.b64decode(blob['content'])
                valid = _same(old, remote, relative)
            else:
                valid = (old is None and entry is None) or (old is not None and entry is not None and git_hash(old) == entry['sha'])
            if not valid:
                raise GitHubSyncError('앱과 GitHub의 최신 기록이 다릅니다. 자동 덮어쓰기를 중단했습니다. 앱 ZIP을 백업한 뒤 GitHub 기록과 비교·반영하고 앱을 다시 시작해주세요.')

    def commit(self, changes, message):
        entries = []
        for relative, raw in changes.items():
            path = self.repo_path(relative)
            if raw is None:
                if path in self.entries:
                    entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': None})
            else:
                sha = self.api('POST', '/git/blobs', json={'content': base64.b64encode(raw).decode(), 'encoding': 'base64'})['sha']
                entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': sha})
        if not entries:
            return None
        tree = self.api('POST', '/git/trees', json={'base_tree': self.base_tree, 'tree': entries})['sha']
        commit = self.api('POST', '/git/commits', json={'message': message, 'tree': tree, 'parents': [self.parent]})['sha']
        try:
            self.api('PATCH', '/git/refs/heads/' + quote(self.branch, safe='/'), json={'sha': commit, 'force': False})
        except GitHubSyncError:
            # A timeout after GitHub accepted the update must not be treated as failure.
            if self.head() != commit:
                raise
        return commit


def configured_client():
    # Local-only work requires an explicit switch. Default is fail-closed autosave.
    if _setting('GITHUB_SYNC_ENABLED', True) is False:
        return None
    return GitHubSync(str(_setting('GITHUB_TOKEN')), str(_setting('GITHUB_REPO', 'empasend-poop/Sennie')),
                      str(_setting('GITHUB_BRANCH')), str(_setting('GITHUB_BASE_PATH', 'sennie')))


def success_message(action):
    if _setting('GITHUB_SYNC_ENABLED', True) is False:
        return action + ' 앱에만 저장했습니다. ZIP 백업과 GitHub 반영이 필요합니다.'
    return action + ' GitHub에도 자동 반영했습니다. 앱이 재배포되면 잠시 뒤 새로고침해주세요.'
