import os
import json
from dotenv import load_dotenv
from github import Github
from collections import Counter

with open("config.json", "r") as f:
    config = json.load(f)

with open('config.json') as config_file:
    config = json.load(config_file)

def get_repos(g: Github):
    exclude_organizations = config.get("exclude_organizations", True)
    repos = [repo for repo in g.get_user().get_repos(type="public") if repo.visibility == "public"]
    if exclude_organizations:
        repos = [repo for repo in repos if repo.owner.type != "Organization"]
    return repos

def get_lines_of_code(g: Github) -> int:
    total_lines = 0
    for repo in get_repos(g):
        if repo.visibility == "public":  # Double check visibility again!
            try:
                languages = repo.get_languages()
                total_lines += sum(languages.values())
            except Exception:
                continue
    return total_lines

def get_languages(g: Github) -> dict:
    languages = Counter()
    for repo in get_repos(g):
        if repo.visibility == "public":  # Double check visibility again!
            try:
                for lang, bytes_count in repo.get_languages().items():
                    languages[lang] += bytes_count
            except Exception:
                continue
    return dict(languages)

def format_languages(languages: dict) -> str:
    sorted_lang = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    max_languages = config.get("max_languages", -1)
    if max_languages != -1:
        sorted_lang = sorted_lang[:max_languages]
    return '\n'.join([f"- {lang}: {bytes_count} bytes of code" for lang, bytes_count in sorted_lang]) # The GitHUB API returns the bytes of code written in a language, not the lines of code

def fetch_stats(g: Github) -> dict:
    user = g.get_user()
    total_commits = 0
    total_issues = 0
    total_prs = 0

    for repo in get_repos(g):
        if not repo.fork and repo.visibility == "public":  # Check both fork and visibility
            try:
                total_commits += repo.get_commits().totalCount
                total_issues += repo.get_issues().totalCount
                total_prs += repo.get_pulls().totalCount
            except Exception:
                continue

    return {
        "username": user.login,
        "followers": user.followers,
        "following": user.following,
        "public_repos": user.public_repos,
        "public_gists": user.public_gists,
        "total_stars": sum([repo.stargazers_count for repo in get_repos(g)]),
        "bytes_of_code": get_lines_of_code(g),
        "bio": user.bio,
        "location": user.location,
        "company": user.company,
        "email": user.email,
        "website": user.blog,
        "hireable": user.hireable,
        "created_at": user.created_at.strftime("%d-%m-%Y"),
        "updated_at": user.updated_at.strftime("%d-%m-%Y"),
        "languages": format_languages(get_languages(g)),
        "total_commits": total_commits,
        "total_issues": total_issues,
        "total_prs": total_prs,
    }