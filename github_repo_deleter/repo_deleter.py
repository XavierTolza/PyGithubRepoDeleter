from argparse import ArgumentParser
from os import getenv

import inquirer
from github import Github, BadCredentialsException


def run_delete(token):
    g = Github(token)

    try:
        user = g.get_user()
        choices = []
        repos_unsorted = user.get_repos()
        repos = sorted(repos_unsorted, key=lambda x: x.updated_at)
    except BadCredentialsException:
        print("Invalid token. Make sure the token is correct "
              "and you have the repo and delete_repo rights")
        return
    for repo in repos:
        if repo.permissions.admin:
            choices.append(repo.full_name)

    if not choices:
        print("No repositories with admin permissions found.")
        return

    questions = [
        inquirer.Checkbox('repos',
                          message="Select repos to delete",
                          choices=choices),
    ]

    answers = inquirer.prompt(questions)
    if not answers:  # User cancelled
        print("Aborted")
        return

    to_delete_names = answers["repos"]

    if len(to_delete_names):
        to_delete = [repo for repo in repos
                     if repo.full_name in to_delete_names]
        to_delete_str = "\n\t".join(["- " + i for i in to_delete_names])

        confirm_message = (f'Please confirm you want to delete '
                           f'the following repositories:\n\t{to_delete_str}')
        confirm_questions = [
            inquirer.List('choice',
                          message=confirm_message,
                          choices=["NO", "YES"]),
        ]

        confirm_answers = inquirer.prompt(confirm_questions)
        if not confirm_answers:  # User cancelled
            print("Aborted")
            return

        confirm = confirm_answers["choice"] == "YES"

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
        inquirer.Text('token',
                      message='Enter your github token '
                              '(https://github.com/settings/tokens)'),
    ]
    parser = ArgumentParser()
    parser.add_argument("--token", help="Github token")
    token = None
    while token is None or token == "":
        parsed_token = parser.parse_args().token
        env_token = getenv("GITHUB_TOKEN")
        if parsed_token:
            token = parsed_token
        elif env_token:
            token = env_token
        else:
            prompt_result = inquirer.prompt(token_questions)
            if prompt_result:
                token = prompt_result["token"]
            else:
                # User cancelled prompt
                break
    return token


def main():
    token = get_token()
    if token:
        run_delete(token)
        print("Finished")
    else:
        print("No token provided. Exiting.")


if __name__ == '__main__':
    main()
