from argparse import ArgumentParser
from os import getenv

from PyInquirer import prompt
from github import Github, BadCredentialsException


def run_delete(token):
    g = Github(token)

    try:
        user = g.get_user()
        choices = []
        questions = [{
            'type': 'checkbox',
            'message': 'Select repos to delete',
            'name': 'repos',
            'choices': choices,
        }]
        repos_unsorted = user.get_repos()
        repos = sorted(repos_unsorted, key=lambda x: x.updated_at)
    except BadCredentialsException:
        print("Invalid token. Make sure the token is correct and you have the repo and delete_repo rights")
        return
    for repo in repos:
        if repo.permissions.admin:
            choices.append({"name": repo.full_name})

    to_delete_names = prompt(questions)["repos"]

    if len(to_delete_names):
        to_delete = [repo for repo in repos if repo.full_name in to_delete_names]
        to_delete_str = "\n\t".join(["- " + i for i in to_delete_names])

        confirm = prompt([{
            'type': 'list',
            'message': f'Please confirm you want to delete the following repositories:\n\t{to_delete_str}',
            'name': 'choice',
            'choices': ["NO", "YES"],
        }])["choice"] == "YES"

        if not confirm:
            print("Aborted")
            return

        for repo in to_delete:
            print(f"Deleting {repo.full_name}...")
            repo.delete()
            print("OK")
    else:
        print("No repo to delete")


def get_token():
    token_questions = [
        {
            'type': 'input',
            'name': 'token',
            'message': 'Enter your github token (https://github.com/settings/tokens)',
        }
    ]
    parser = ArgumentParser()
    parser.add_argument("--token", help="Github token")
    token = None
    while token is None or token == "":
        token = parser.parse_args().token or getenv("GITHUB_TOKEN") or prompt(token_questions)["token"]
    return token


def main():
    token = get_token()
    run_delete(token)
    print("Finished")


if __name__ == '__main__':
    main()
