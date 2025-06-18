from github import Github
import json
import os

class GithubHandler:
    def __init__(self):
        self.g = Github(os.getenv('GIST_TOKEN'))
        self.repo = self.g.get_repo(os.getenv('GIST_REPO'))
        self.file_path = os.getenv('GIST_FILE_PATH')
    
    def get_json_file(self, branch='main'):
        file_content = self.repo.get_contents(self.file_path, ref=branch)
        return json.loads(file_content.decoded_content.decode())
    
    def update_json_file(self, update_data, commit_message=".", branch='main'):
        updated_content = json.dumps(update_data, indent=4)
        file_content = self.repo.get_contents(self.file_path, ref=branch)
        return self.repo.update_file(file_content.path, commit_message, updated_content, file_content.sha, branch=branch)

# def get_json_from_github(repo, file_path, branch='main'):
#     file_content = repo.get_contents(file_path, ref=branch)
#     return json.loads(file_content.decoded_content.decode())

# def update_json_file(github_token, repo_name, file_path, update_data, branch='main'):
#     g = Github(github_token)
#     repo = g.get_repo(repo_name)
    
    
#     # Convert updated JSON data to string
#     updated_content = json.dumps(update_data, indent=4)
    
#     # Get the file from the repository
#     file_content = repo.get_contents(file_path, ref=branch)
    
#     # Update the file in the repository
#     repo.update_file(file_content.path, "Update JSON file", updated_content, file_content.sha, branch=branch)

# Example usage
# if __name__ == "__main__":
#     github_token = "your_github_token"
#     repo_name = "your_github_username/your_repo_name"
#     file_path = "path/to/your/file.json"
#     update_data = {
#         "new_key": "new_value"
#     }
    
#     update_json_file(github_token, repo_name, file_path, update_data)

