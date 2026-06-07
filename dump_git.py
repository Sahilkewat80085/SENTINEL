import subprocess
import json

def main():
    # Run git log
    cmd = ["git", "log", "--numstat", "--pretty=format:COMMIT_START|%H|%an|%ae|%aI|%s"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if res.returncode != 0:
        print("Git log command failed:", res.stderr)
        return

    commits = []
    current_commit = None

    lines = res.stdout.splitlines()
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("COMMIT_START|"):
            if current_commit:
                commits.append(current_commit)
            parts = line.split("|", 5)
            sha = parts[1]
            author_name = parts[2]
            author_email = parts[3]
            commit_date = parts[4]
            message = parts[5] if len(parts) > 5 else ""
            
            author_username = author_email.split("@")[0] if "@" in author_email else author_name.lower().replace(" ", "")

            current_commit = {
                "sha": sha,
                "author_name": author_name,
                "author_email": author_email,
                "author_username": author_username,
                "commit_date": commit_date,
                "message": message,
                "files": []
            }
        else:
            parts = line.split()
            if len(parts) >= 3 and current_commit is not None:
                add_str, del_str, file_path = parts[0], parts[1], parts[2]
                try:
                    additions = int(add_str)
                except ValueError:
                    additions = 0
                try:
                    deletions = int(del_str)
                except ValueError:
                    deletions = 0
                
                change_type = "MODIFIED"
                
                current_commit["files"].append({
                    "file_path": file_path,
                    "change_type": change_type,
                    "additions": additions,
                    "deletions": deletions
                })

    if current_commit:
        commits.append(current_commit)

    with open("backend/commits.json", "w", encoding="utf-8") as f:
        json.dump(commits, f, indent=2)

    print(f"Successfully dumped {len(commits)} commits to backend/commits.json!")

if __name__ == "__main__":
    main()
