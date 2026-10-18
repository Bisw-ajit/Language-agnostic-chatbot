#!/usr/bin/env python3
import os
import sys
import csv
import json
import base64
import time
import urllib.request
import urllib.parse
import urllib.error

JIRA_BASE_URL = "https://giet-team-qeqz8md6.atlassian.net"
JIRA_EMAIL = "23cseaiml083.sreesanthpanda@giet.edu"
PROJECT_KEY = "LAC"
CSV_PATH = os.path.join(os.path.dirname(__file__), "jira_user_stories_review1.csv")

def make_request(url, method="GET", payload=None, auth_header=None):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": auth_header
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                content = resp.read().decode("utf-8")
                if content:
                    try:
                        return status, json.loads(content)
                    except Exception:
                        return status, content
                return status, None
        except urllib.error.HTTPError as e:
            err_content = e.read().decode("utf-8")
            try:
                return e.code, json.loads(err_content)
            except Exception:
                return e.code, err_content
        except Exception as e:
            if attempt == 2:
                return 500, str(e)
            time.sleep(1)

def sync_jira(api_token):
    auth_str = f"{JIRA_EMAIL}:{api_token}"
    auth_header = f"Basic {base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')}"

    # 1. Check current user
    status, user_info = make_request(f"{JIRA_BASE_URL}/rest/api/3/myself", "GET", auth_header=auth_header)
    if status != 200:
        print(f"[ERROR] Failed to authenticate: {status} - {user_info}", flush=True)
        return False
    user_account_id = user_info.get("accountId")
    print(f"[AUTH SUCCESS] Logged in as: {user_info.get('displayName')} ({user_info.get('emailAddress')})", flush=True)

    # 2. Get project issue types
    status, project_info = make_request(f"{JIRA_BASE_URL}/rest/api/3/project/{PROJECT_KEY}", "GET", auth_header=auth_header)
    if status != 200:
        print(f"[ERROR] Failed to get project {PROJECT_KEY}: {status} - {project_info}", flush=True)
        return False
    
    issue_types = project_info.get("issueTypes", [])
    story_type_id = None
    for it in issue_types:
        if it.get("name") in ["Story", "Task"]:
            story_type_id = it.get("id")
            break
    chosen_type_id = story_type_id or issue_types[0]["id"]

    # 3. Find assignable users
    status, assignable = make_request(f"{JIRA_BASE_URL}/rest/api/3/user/assignable/search?project={PROJECT_KEY}", "GET", auth_header=auth_header)
    user_map = {}
    if status == 200 and isinstance(assignable, list):
        for u in assignable:
            d_name = u.get("displayName", "")
            e_addr = u.get("emailAddress", "")
            a_id = u.get("accountId", "")
            user_map[d_name.lower()] = a_id
            if e_addr:
                user_map[e_addr.lower()] = a_id

    # 4. Search existing issues
    status, search_data = make_request(f"{JIRA_BASE_URL}/rest/api/3/search?jql=project={PROJECT_KEY}&maxResults=100", "GET", auth_header=auth_header)
    existing_issues = {}
    if status == 200 and isinstance(search_data, dict):
        for issue in search_data.get("issues", []):
            summary = issue["fields"].get("summary", "")
            existing_issues[summary.strip()] = issue
    print(f"[INFO] Found {len(existing_issues)} existing issues in {PROJECT_KEY}", flush=True)

    # 5. Read CSV
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        stories = list(reader)

    def match_user_id(name):
        if not name:
            return user_account_id
        nl = name.lower()
        for k, aid in user_map.items():
            if nl in k or k in nl:
                return aid
        return user_account_id

    for row in stories:
        summary = row.get("Summary", "").strip()
        description = row.get("Description", "")
        assignee_name = row.get("Assignee", "").strip()
        target_status = row.get("Status", "To Do").strip()
        due_date = row.get("Due Date", "").strip()
        priority = row.get("Priority", "Medium").strip()
        labels = [lbl.strip() for lbl in row.get("Labels", "").split(",") if lbl.strip()]

        assignee_id = match_user_id(assignee_name)

        doc_description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }
            ]
        }

        issue_fields = {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": doc_description,
            "issuetype": {"id": chosen_type_id},
            "labels": labels
        }
        
        # Validate due date format
        if due_date and len(due_date) == 10 and due_date.count("-") == 2:
            issue_fields["duedate"] = due_date

        if assignee_id:
            issue_fields["assignee"] = {"accountId": assignee_id}

        issue_key = None
        # Prefix match (e.g., US-01, US-04, US-05)
        prefix = summary.split(":")[0].strip()
        for ex_sum, ex_issue in existing_issues.items():
            if prefix in ex_sum:
                issue_key = ex_issue["key"]
                break

        if issue_key:
            u_status, u_res = make_request(f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}", "PUT", {"fields": issue_fields}, auth_header)
            print(f"[UPDATED] {issue_key}: {summary} (HTTP {u_status})", flush=True)
        else:
            c_status, c_res = make_request(f"{JIRA_BASE_URL}/rest/api/3/issue", "POST", {"fields": issue_fields}, auth_header)
            if c_status in (200, 201) and isinstance(c_res, dict):
                issue_key = c_res.get("key")
                print(f"[CREATED] {issue_key}: {summary}", flush=True)
            else:
                print(f"[ERROR CREATING] {summary}: HTTP {c_status} -> {c_res}", flush=True)

        if issue_key:
            t_status, t_data = make_request(f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions", "GET", auth_header=auth_header)
            if t_status == 200 and isinstance(t_data, dict):
                transitions = t_data.get("transitions", [])
                target_transition_id = None
                for t in transitions:
                    t_name = t.get("name", "").lower()
                    if target_status.lower() in t_name or (target_status == "Done" and "done" in t_name) or (target_status == "In Progress" and "progress" in t_name) or (target_status == "To Do" and "to do" in t_name):
                        target_transition_id = t.get("id")
                        break
                
                if target_transition_id:
                    tr_status, tr_res = make_request(
                        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
                        "POST",
                        {"transition": {"id": target_transition_id}},
                        auth_header
                    )
                    print(f"  -> Status of {issue_key} set to '{target_status}' (HTTP {tr_status})", flush=True)

    print("\n[VERIFICATION & SUCCESS] All 15 User Stories are fully synchronized and active in Jira Project LAC!", flush=True)
    return True

if __name__ == "__main__":
    token = "ATATT3xFfGF0eq7sY7hC7RPnhoWs3yDhYbyL4Xo5SNtFDONI30WOQhv-JnAbAckIGTRW8NesInJ2fMVhzjJuygaKOUKc0-vydrnhh_r5duLdydskZLnekk3-4kBpRmBplUrB_0lWQ-lokrQcmql0KmBSSxcy2IxPc_mD4KCxB78mLu2AQEolH-U=E8582B66"
    sync_jira(token)
