import requests
from datetime import datetime
import os

github_actor = os.getenv('github_actor')

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
        'commit': 'Not fetched yet'  # 추가로 구현 진행중
    }

    return user_info

# GitHub API를 통해 사용자 정보 가져오기
user_info = fetch_user_info(github_actor)

# 결과 출력
print(user_info)
