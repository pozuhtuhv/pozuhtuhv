import os
import requests
from collections import defaultdict
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib

github_actor = os.getenv('github_actor')

# svg 폴더 없으면 만들기
os.makedirs('svg', exist_ok=True)

# 기존 SVG 파일 경로 및 출력 SVG 파일 경로
origin_svg_file_path = 'svg/edit_svg.svg'
output_svg_file_path = 'svg/main_svg.svg'

# GitHub API에서 유저 정보를 가져오기 위한 함수
def fetch_user_info(username):
    user_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos"
    
    user_data = requests.get(user_url).json()
    repos_data = requests.get(repos_url).json()

    # 가입일자 계산
    created_at = datetime.strptime(user_data['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    today = datetime.now()
    account_age = today - created_at
    age_years = account_age.days // 365
    age_months = (account_age.days % 365) // 30
    age_days = (account_age.days % 365) % 30
    
    # 퍼블릭 레포지토리 수
    total_repos = len(repos_data)

    # 언어 비중 계산
    language_stats = {}
    for repo in repos_data:
        if repo['language'] in language_stats:
            language_stats[repo['language']] += 1
        else:
            language_stats[repo['language']] = 1

    # 총 사이즈(KB)를 MB로 변환
    total_size_kb = sum(repo['size'] for repo in repos_data)
    total_size_mb = total_size_kb / 1024  # 1MB = 1024KB
    
    # 총 별 갯수
    total_stars = sum(repo['stargazers_count'] for repo in repos_data)

    # 커밋 통계 가져오기
    commit_stats = fetch_commit_statistics(username)

    # 시간대별 커밋 정보 형식화
    commit_info = ', '.join(f'{k}: {v}' for k, v in commit_stats.items())
    
    user_info = {
        'created_at': f'{age_years}year {age_months}month {age_days}day',
        'name': user_data['name'],
        'login': user_data['login'],
        'uid': user_data['id'],
        'followers': user_data['followers'],
        'following': user_data['following'],
        'total_repos': total_repos,
        'size': f'{total_size_mb:.2f} MB',  # MB 단위로 표시
        'stars': total_stars,
        'languages': language_stats,
        'commit': commit_info  # 커밋 정보 추가
    }

    return user_info

# 사용자의 저장소 목록 가져오기
def get_repos(USER_NAME):
    repos = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/users/{USER_NAME}/repos?per_page={per_page}&page={page}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()

        if len(data) == 0:
            break

        repos.extend(data)
        page += 1

    return repos

# 특정 저장소의 커밋 가져오기
def get_commits(repo_full_name):
    commits = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page={per_page}&page={page}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()

        if len(data) == 0:
            break

        for commit in data:
            commit['repository'] = {'full_name': repo_full_name}  # 저장소 정보 추가

        commits.extend(data)
        page += 1

    return commits

# 커밋 시간을 기준으로 시간대 분류
def categorize_commit_time(commit_time):
    hour = commit_time.hour
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Daytime"
    elif 18 <= hour < 24:
        return "Evening"
    else:
        return "Night"

# 커밋 통계 계산
def fetch_commit_statistics(username):
    repos = get_repos(username)

    # 모든 커밋 가져오기
    all_commits = []
    for repo in repos:
        repo_full_name = repo['full_name']
        commits = get_commits(repo_full_name)
        all_commits.extend(commits)

    # 시간대별 커밋 수 집계
    commit_times = defaultdict(int)
    for commit in all_commits:
        commit_time = datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
        time_category = categorize_commit_time(commit_time)
        commit_times[time_category] += 1

    return commit_times

# GitHub API를 통해 사용자 정보 가져오기
if github_actor:
    user_info = fetch_user_info(github_actor)
    print(user_info)
else:
    print("github_actor 환경 변수를 설정하세요.")

# 해시 계산 함수
def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

# 유저 정보를 업데이트하는 함수
def update_svg(user_info, origin_svg_file_path, filename):
    # SVG 파일 읽기
    tree = ET.parse(origin_svg_file_path)
    root = tree.getroot()
    
    # XML 네임스페이스 설정
    ns = {'svg': 'http://www.w3.org/2000/svg', 'xhtml': 'http://www.w3.org/1999/xhtml'}
    
    # 기본 정보를 수정 (user info 출력 부분)
    root.find(".//xhtml:div[@class='text-line line4']", ns).text = f"C:\\Users\\{user_info['login']}>user info"
    
    # 유저 정보 부분 수정
    root.find(".//xhtml:div[@class='text-line line7']", ns).text = f"created : {user_info['created_at']}"
    root.find(".//xhtml:div[@class='text-line line8']", ns).text = f"name : {user_info['name']}"
    root.find(".//xhtml:div[@class='text-line line9']", ns).text = f"id : {user_info['login']} / uid : {user_info['uid']}"
    root.find(".//xhtml:div[@class='text-line line10']", ns).text = f"follows: {user_info['followers']} following: {user_info['following']}"
    root.find(".//xhtml:div[@class='text-line line12']", ns).text = f"C:\\Users\\{user_info['login']}>user info"

    # 레포지토리 정보 수정
    root.find(".//xhtml:div[@class='text-line line15']", ns).text = f"total : {user_info['total_repos']} - size : {user_info['size']} - stared : {user_info['stars']}"
    root.find(".//xhtml:div[@class='text-line line16']", ns).text = f"activity times : {user_info['commit']}"
    
    # 언어 비율 정보 수정
    languages_str = ', '.join([f"{k}: {v}" for k, v in user_info['languages'].items()])
    root.find(".//xhtml:div[@class='text-line line17']", ns).text = f"languages : {languages_str}"


    temp_filename = f"{filename}.temp"
    with open(temp_filename, 'w', encoding='utf-8') as temp_file:
        temp_file.write(output_svg_file_path, encoding="utf-8", xml_declaration=True)
        
    # 기존 파일이 있는 경우 해시를 비교하여 내용이 동일한지 확인
    if os.path.exists(filename) and calculate_file_hash(filename) == calculate_file_hash(temp_filename):
        print(f'{filename} 파일의 내용이 동일하여 덮어쓰지 않습니다.')
        os.remove(temp_filename)  # 임시 파일 삭제
    else:
        os.rename(temp_filename, filename)
        print(f'{filename} 저장 완료')

# SVG 파일 업데이트
update_svg(user_info, origin_svg_file_path, output_svg_file_path)
