"""
Originally from: https://github.com/MickJerin12/Zenhub-to-jira
Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.

"""
import csv
import datetime
import requests

GITHUB_USER = ''
GITHUB_PASSWORD = ''
AUTH = (GITHUB_USER, GITHUB_PASSWORD)

ZENHUB_AUTHENTICATION_TOKEN = ''
ZENHUB_REPO_ID = ''
ZENHUB_HEADERS = {
    'X-Authentication-Token': '',
}
REPO = ''  # format is username/repo


def iterate_pages(repository):
    """
    Make request for 100 issues starting from the first page until the last page is reached
    Every request text is appended to 'results'
    :return JSON object with all issues
    """
    results = []
    page_number = 1
    # per_page can be moved into a var in case you need less than 100 issues per request
    issues = 'https://api.github.com/repos/{}/issues?state=all&page={}&per_page=100'.format(repository, page_number)
    request = requests.get(issues, auth=AUTH)
    results.append(request.json())
    print("Link",request.headers)

    # make requests until the 'last' url is reached and increase the page number by 1 for each request
    #while 'last' in request.headers['link'] and 'next' in request.headers['link']:
        #page_number += 1
    issues = 'https://api.github.com/repos/{}/issues?state=all&page={}&per_page=100'.format(repository, page_number)
    request = requests.get(issues, auth=AUTH)
    results.append(request.json())
    return results


def get_comments_max_nr():
    """
    Get maximum number of comments for one issue in order to write header columns when creating the CSV file
    :return: count of the max comments per issue
    """
    comments_list = []
    for result in total_result:
        for issue in result:
            if issue.get('pull_request') is None:
                if issue['comments'] > 0:
                    comments_list.append(issue['comments'])
    return max(comments_list)


def get_labels_nr():
    """
    Get number of labels for the repo. Used to write header columns when creating the CSV file
    Appends each unique label found to 'labels_list'
    :returns length of the labels_list
    """
    labels_list = []
    for result in total_result:
        for issue in result:
            if issue.get('pull_request') is None:
                for label in issue['labels']:
                    if label is not None:
                        # Check if the label name is already appended to 'labels_list'
                        if label['name'] not in labels_list:
                            labels_list.append(label['name'])
    return len(labels_list)

def handling_epic(issue_type,zenhub_json_object_epic,issue,epic_name,epic_link,issue_resolution,issue_milestone,resolved_at,assignee):
    parent_id=None
    issue_id=None
    print("description is", issue)
    if 'pipeline' in zenhub_json_object_epic.keys() :
        if('name' in zenhub_json_object_epic['pipeline'].keys()):
            issue_status = zenhub_json_object_epic['pipeline']['name']
        else:
            issue_status=None
    else:
        issue_status='closed'
    if zenhub_json_object_epic.get('estimate'):
        issue_estimation = zenhub_json_object_epic['estimate']['value']
    else:
        issue_estimation = 0
    if issue.get('assignee') is not None:
        assignee = issue['assignee']['login']
        reporter = issue['user']['login']
    if issue.get('milestone') is not None:
        issue_milestone = issue['milestone']['title']
    date_format_rest = '%Y-%m-%dT%H:%M:%SZ'
    date_format_jira = '%d/%b/%y %l:%M %p'
    date_created = datetime.datetime.strptime(issue['created_at'], date_format_rest)
    created_at = date_created.strftime(date_format_jira)
    date_updated = datetime.datetime.strptime(issue['updated_at'], date_format_rest)
    updated_at = date_updated.strftime(date_format_jira)
    if issue.get('closed_at') is not None:
        date_resolved = datetime.datetime.strptime(issue['closed_at'], date_format_rest)
        resolved_at = date_resolved.strftime(date_format_jira)
    comments_list = []
    if issue['comments'] > 0:
        comments_request = requests.get(issue['comments_url'], auth=AUTH)
        for comment in comments_request.json():
            issue_comments = 'Username: {} Content: {};'.format(comment['user']['login'], comment['body'])
            comments_list.append(issue_comments)
    comments_list = comments_list + [''] * (comments_max_nr - len(comments_list))
    labels_list = []
    labels = issue['labels']
    for label in labels:
        label_name = label['name']
        if(label_name == "Enhancement"):
            issue_type="Task"
        elif(label_name=="L1 Bug"):
            issue_type="L1 Bug"
        elif(label_name=="L2 Bug"):
            issue_type="L2 Bug"
        labels_list.append(label_name)
        if label_name == 'wontfix':
            issue_resolution = "won\'t do"
        elif label_name == 'duplicate':
            issue_resolution = 'duplicate'
        elif label_name == "bug":
            issue_resolution = 'bug'
    labels_list = labels_list + [None] * (labels_max_nr - len(labels_list))
    if issue:
        issue_id = str(issue['title'].encode('utf-8'))+"_id"
    if issue_status == 'Closed':
        issue_resolution = 'Done'
    print("Number: ", issue['number'])
    print("Title: ", issue['title'].encode('utf-8'))
    print("Type: ", issue_type)
    print("Status: ", issue_status)
    print("Resolution: ", issue_resolution)
    print("Label name: ", *labels_list)
    print("Body: ", issue['body'].encode('utf-8'))
    print("Assignee", assignee)
    print("Reporter", reporter)
    print("Created at: ", created_at)
    print("Updated at: ", updated_at)
    print("Resolved at:", resolved_at)
    print("Estimation: ", issue_estimation)
    print("Fix Version / Milestone: ", issue_milestone)
    print("Comments: ", *comments_list)
    print("Epic Name", epic_name )
    print("Epic Link", epic_link)
    print("writing into csv")
    print("issue_id", issue_id)
    print("parent_id", parent_id)
    csvout.writerow([
        issue['number'],  # Key
        issue['title'].strip(),  # Summary
        issue_type,  # Type
        issue_status,  # Status
        issue_resolution,  # resolution
        issue_milestone,  # Milestone, Fix Version
        issue['body'].strip(),  # Description
        assignee,  # assignee
        reporter,  # reporter
        created_at,  # created
        updated_at,  # updated
        resolved_at,  # Date issue closed at
        issue_estimation,  # estimate
        epic_name.strip(),
        epic_link,
        issue_id,
        parent_id,
        *labels_list,  # labels (multiple labels in multiple columns)
        *comments_list, # comments (multiple comments in multiple columns)
    ])
    bad_chars = ['#', "-"]
    body = str(issue['body'])
    if(len(body)>5):
        print("body is",body)
        for i in bad_chars:
            test_string = body.replace(i, '')
        resultant_string = test_string.split("\n")[1:]
        for task in resultant_string:
          if task:
            if '[x]' in task:
                task = task.split('[x]')
                print("splitted task is",task)
                status = "closed"
                issue_title = task[1]
                issue_body = task[1]
            elif '[ ]' in task:
                task=task.split('[ ]')
                status = issue_status
                issue_title = task[1]
                issue_body = task[1]
            else:
                status = issue_status
                issue_title = task
                issue_body = task
            parent_id = str(issue['title'].encode('utf-8'))+"_id"
            issue_id = None
            csvout.writerow([
                issue['number'],  # Key
                issue_title,  # Summary
                issue_type,  # Type
                status,  # Status
                issue_resolution,  # resolution
                issue_milestone,  # Milestone, Fix Version
                issue_body,  # Description
                assignee,  # assignee
                reporter,  # reporter
                created_at,  # created
                updated_at,  # updated
                resolved_at,  # Date issue closed at
                issue_estimation,  # estimate
                epic_name,  # epic_name
                epic_link,  # epic_link
                issue_id,
                parent_id,
                # labels (multiple labels in multiple columns)
                *labels_list,
                *comments_list,  # comments (multiple comments in multiple columns)
            ])

def print_remaining(child,issue,issue_status,issue_type,issue_estimation,epic_name,issue_resolution,resolved_at,issue_milestone,assignee,uncompleted):
    parent_id = None
    issue_id=None
    print("calling")
    issue_number=issue['number']
    for index in range(len(uncompleted)):
        if issue_number in uncompleted[index].keys():
            print("uncompleted with index", uncompleted[index][issue_number]['value'])
            epic_link = uncompleted[index][issue_number]['value']
    print("epic_link is",epic_link)
    if issue.get('assignee') is not None:
        assignee = issue['assignee']['login']
        reporter = issue['user']['login']
    else:
        assignee=None
        reporter=None
    if issue.get('milestone') is not None:
        issue_milestone = issue['milestone']['title']
    date_format_rest = '%Y-%m-%dT%H:%M:%SZ'
    date_format_jira = '%d/%b/%y %l:%M %p'
    date_created = datetime.datetime.strptime(issue['created_at'], date_format_rest)
    created_at = date_created.strftime(date_format_jira)
    date_updated = datetime.datetime.strptime(issue['updated_at'], date_format_rest)
    updated_at = date_updated.strftime(date_format_jira)
    if issue.get('closed_at') is not None:
        date_resolved = datetime.datetime.strptime(issue['closed_at'], date_format_rest)
        resolved_at = date_resolved.strftime(date_format_jira)
    comments_list = []
    if issue['comments'] > 0:
        comments_request = requests.get(issue['comments_url'], auth=AUTH)
        for comment in comments_request.json():
            issue_comments = 'Username: {} Content: {};'.format(comment['user']['login'], comment['body'])
            comments_list.append(issue_comments)
    comments_list = comments_list + [''] * (comments_max_nr - len(comments_list))
    labels_list = []
    labels = issue['labels']
    for label in labels:
        label_name = label['name']
        labels_list.append(label_name)
        if label_name == 'wontfix':
            issue_resolution = "won\'t do"
        elif label_name == 'duplicate':
            issue_resolution = 'duplicate'
        elif label_name == "bug":
            issue_resolution = 'bug'
    labels_list = labels_list + [None] * (labels_max_nr - len(labels_list))
    if issue:
        issue_id = str(issue['title'].encode('utf-8'))+"_id"
    if issue_status == 'Closed':
        issue_resolution = 'Done'
    if issue:
        print("Number: ", issue['number'])
        print("Title: ", issue['title'].encode('utf-8'))
        print("Type: ", issue_type)
        print("Status: ", issue_status)
        print("Resolution: ", issue_resolution)
        print("Label name: ", *labels_list)
        print("Body: ", issue['body'].encode('utf-8'))
        print("Assignee", assignee)
        print("Reporter", reporter)
        print("Created at: ", created_at)
        print("Updated at: ", updated_at)
        print("Resolved at:", resolved_at)  
        print("Estimation: ", issue_estimation)
        print("Fix Version / Milestone: ", issue_milestone)
        print("Comments: ", *comments_list)
        print("Epic Name", epic_name )
        print("Epic Link",epic_link)
        print("issue_id", issue_id)
        print("parent_id", parent_id)
        csvout.writerow([
            issue['number'],  # Key
            issue['title'].strip(),  # Summary
            issue_type,  # Type
            issue_status,  # Status
            issue_resolution,  # resolution
            issue_milestone,  # Milestone, Fix Version
            issue['body'].strip(),  # Description
            assignee,  # assignee
            reporter,  # reporter
            created_at,  # created
            updated_at,  # updated
            resolved_at,  # Date issue closed at
            issue_estimation,  # estimate
            epic_name,
            epic_link,
            issue_id,
            parent_id,
            *labels_list,  # labels (multiple labels in multiple columns)
            *comments_list, # comments (multiple comments in multiple columns)
        ])
        bad_chars = ['#', "-"]
        body = str(issue['body'])
        if(body):
            for i in bad_chars:
                test_string = body.replace(i, '')
            resultant_string = test_string.split("\n")[1:]
            for task in resultant_string:

                if task and task[0]!='#':
                    if '[x]' in task:
                        print("task is",task)
                        task = task.split('[x]')
                        print("splitted task is", task)
                        status = "closed"
                        issue_title = task[1]
                        issue_body = task[1]
                    elif '[ ]' in task:
                        task=task.split('[ ]')
                        print("Null task is",task)
                        status = issue_status
                        issue_title = task[1]
                        issue_body = task[1]
                    else:
                        status = issue_status
                        issue_title = task
                        issue_body = task
                    parent_id = str(issue['title'].encode('utf-8'))+"_id"
                    issue_id = None
                    csvout.writerow([
                        issue['number'],  # Key
                        issue_title,  # Summary
                        issue_type,  # Type
                        status,  # Status
                        issue_resolution,  # resolution
                        issue_milestone,  # Milestone, Fix Version
                        issue_body,  # Description
                        assignee,  # assignee
                        reporter,  # reporter
                        created_at,  # created
                        updated_at,  # updated
                        resolved_at,  # Date issue closed at
                        issue_estimation,  # estimate
                        epic_name,  # epic_name
                        epic_link,  # epic_link
                        issue_id,
                        parent_id,
                        # labels (multiple labels in multiple columns)
                        *labels_list,
                        # comments (multiple comments in multiple columns)
                        *comments_list,
                    ])


def handling_issue(issue_type,child,issue,epic_name,epic_link,issue_resolution,issue_milestone,resolved_at,assignee):
    issue_id=None
    parent_id=None
    epic_name=None
    if 'pipeline' in child.keys() :
        if('name' in child['pipeline'].keys()):
            issue_status = child['pipeline']['name']
        else:
            issue_status=None
    else:
        issue_status='closed'

    if child.get('estimate'):
        issue_estimation = child['estimate']['value']
    else:
        issue_estimation = 0
    if issue:
        for i in uncompleted:
            if issue['number'] in i:
                print_remaining(child,issue,issue_status,issue_type,issue_estimation,epic_name,issue_resolution,resolved_at,issue_milestone,assignee,uncompleted)
                return 0
    if issue:
        if issue.get('assignee') is not None:
            assignee = issue['assignee']['login']
            reporter = issue['user']['login']
        else:
            assignee=None
            reporter=None 
        if issue.get('milestone') is not None:
            issue_milestone = issue['milestone']['title']
        date_format_rest = '%Y-%m-%dT%H:%M:%SZ'
        date_format_jira = '%d/%b/%y %l:%M %p'
        date_created = datetime.datetime.strptime(issue['created_at'], date_format_rest)
        created_at = date_created.strftime(date_format_jira)
        date_updated = datetime.datetime.strptime(issue['updated_at'], date_format_rest)
        updated_at = date_updated.strftime(date_format_jira)
        if issue.get('closed_at') is not None:
            date_resolved = datetime.datetime.strptime(issue['closed_at'], date_format_rest)
            resolved_at = date_resolved.strftime(date_format_jira)
        comments_list = []
        if issue['comments'] > 0:
            comments_request = requests.get(issue['comments_url'], auth=AUTH)
            for comment in comments_request.json():
                issue_comments = 'Username: {} Content: {};'.format(comment['user']['login'], comment['body'])
                comments_list.append(issue_comments)
        comments_list = comments_list + [''] * (comments_max_nr - len(comments_list))
        labels_list = []
        labels = issue['labels']
        for label in labels:
            label_name = label['name']
            labels_list.append(label_name)
            if label_name == 'wontfix':
                issue_resolution = "won\'t do"
            elif label_name == 'duplicate':
                issue_resolution = 'duplicate'
            elif label_name == "bug":
                issue_resolution = 'bug'
        labels_list = labels_list + [None] * (labels_max_nr - len(labels_list))
    if issue:
        issue_id = str(issue['title'].encode('utf-8'))+"_id"
    if issue_status == 'Closed':
        issue_resolution = 'Done'
    if issue:
        print("Number: ", issue['number'])
        print("Title: ", issue['title'].encode('utf-8'))
        print("Type: ", issue_type)
        print("Status: ", issue_status)
        print("Resolution: ", issue_resolution)
        print("Label name: ", *labels_list)
        print("Body: ", issue['body'].encode('utf-8'))
        print("Assignee", assignee)
        print("Reporter", reporter)
        print("Created at: ", created_at)
        print("Updated at: ", updated_at)
        print("Resolved at:", resolved_at)  
        print("Estimation: ", issue_estimation)
        print("Fix Version / Milestone: ", issue_milestone)
        print("Comments: ", *comments_list)
        print("Epic Name", epic_name )
        print("Epic Link",epic_link)
        print("issue_id",issue_id)
        print("parent_id",parent_id)
        csvout.writerow([
            issue['number'],  # Key
            issue['title'].strip(),  # Summary
            issue_type,  # Type
            issue_status,  # Status
            issue_resolution,  # resolution
            issue_milestone,  # Milestone, Fix Version
            issue['body'].strip(),  # Description
            assignee,  # assignee
            reporter,  # reporter
            created_at,  # created
            updated_at,  # updated
            resolved_at,  # Date issue closed at
            issue_estimation,  # estimate
            epic_name,  # epic_name
            epic_link,  # epic_link
            issue_id,
            parent_id, 
            *labels_list,  # labels (multiple labels in multiple columns)
            *comments_list,  # comments (multiple comments in multiple columns)
        ])
        bad_chars = ['#', "-"]
        body = str(issue['body'])
        if(body):
            for i in bad_chars:
                test_string = body.replace(i, '')
            resultant_string = test_string.split("\n")[1:]
            print("resultant string is",resultant_string)
            for task in resultant_string:
                if task:
                    if '[x]' in task:
                        print("task is",task)
                        task = task.split('[x]')
                        print("new task is",task)
                        status = "closed"
                        issue_title = task[1]
                        issue_body = task[1]
                    elif '[ ]' in task:
                        task=task.split('[]')
                        print("Null task is",task)
                        status = issue_status
                        issue_title = task[1]
                        issue_body = task[1]
                    else:
                        status = issue_status
                        issue_title = task[1]
                        issue_body = task[1]
                    parent_id = str(issue['title'].encode('utf-8'))+"_id"
                    issue_id=None
                    csvout.writerow([
                        issue['number'],  # Key
                        issue_title,  # Summary
                        issue_type,  # Type
                        status,  # Status
                        issue_resolution,  # resolution
                        issue_milestone,  # Milestone, Fix Version
                        issue_body,  # Description
                        assignee,  # assignee
                        reporter,  # reporter
                        created_at,  # created
                        updated_at,  # updated
                        resolved_at,  # Date issue closed at
                        issue_estimation,  # estimate
                        epic_name, #epic_name
                        epic_link, #epic_link
                        issue_id,
                        parent_id,
                        *labels_list,  # labels (multiple labels in multiple columns)
                        *comments_list, # comments (multiple comments in multiple columns)
                    ])
    if issue==None:
        uncompleted.append({child['issue_number']:{'value':epic_link}})

def write_epic(results):
    for result in results:
        for issue in result:
            issue_type = None
            issue_resolution = None
            issue_milestone = None
            resolved_at = None
            assignee = None
            epic_name=None
            epic_link=None
            # filter only issues that are not pull requests
            if issue.get('pull_request') is None:
                issue_number = issue['number']

                # make request to zenhub with the issue number
                zenhub_request = requests.get(
                    'https://api.zenhub.io/p1/repositories/{}/issues/{}'.format(ZENHUB_REPO_ID, issue_number),
                    headers=ZENHUB_HEADERS)

                # save the request to a json object
                zenhub_json_object = zenhub_request.json()

                # get 'is_epic' because it throws error if it doesn't exist and the specific issue type will be not
                # assigned at all
                if 'is_epic' in zenhub_json_object.keys():
                    if zenhub_json_object['is_epic'] is True:
                        issue_type = "Epic"
                        epic_name=issue['title']+'_Epic'
                        zenhub_request_epic = requests.get( 'https://api.zenhub.io/p1/repositories/{}/epics/{}'.format(ZENHUB_REPO_ID, issue_number),  headers=ZENHUB_HEADERS)      
                        zenhub_json_object_epic = zenhub_request_epic.json()
                        handling_epic(issue_type,zenhub_json_object_epic,issue,epic_name,epic_link,issue_resolution,issue_milestone,resolved_at,assignee)
                        if 'issues' in zenhub_json_object_epic.keys():
                            for child in zenhub_json_object_epic['issues']:
                                issue_type="story"
                                epic_link=epic_name
                                issue=None
                                handling_issue(issue_type,child,issue,epic_name,epic_link,issue_resolution,issue_milestone,resolved_at,assignee)
def write_issue(results):
     for result in results:
        for issue in result:
            issue_type = None
            issue_resolution = None
            issue_milestone = None
            resolved_at = None
            assignee = None
            epic_name=None
            epic_link=None
            # filter only issues that are not pull requests
            if issue.get('pull_request') is None:
                issue_number = issue['number']

                # make request to zenhub with the issue number
                zenhub_request = requests.get(
                    'https://api.zenhub.io/p1/repositories/{}/issues/{}'.format(ZENHUB_REPO_ID, issue_number),
                    headers=ZENHUB_HEADERS)

                # save the request to a json object
                zenhub_json_object = zenhub_request.json()

                # get 'is_epic' because it throws error if it doesn't exist and the specific issue type will be not
                # assigned at all
                if 'is_epic' in zenhub_json_object.keys():
                    if zenhub_json_object['is_epic'] is False:
                        issue_type = "Story"
                        epic_name=None
                        epic_link=None
                        handling_issue(issue_type,zenhub_json_object,issue,epic_name,epic_link,issue_resolution,issue_milestone,resolved_at,assignee)                 

           
# Call and save the JSON object created by ´iterate_pages()´
total_result = iterate_pages(REPO)
comments_max_nr = get_comments_max_nr()
labels_max_nr = get_labels_nr()
uncompleted=[]
labels_header_list = ['Labels'] * labels_max_nr
comments_header_list = ['Comment Body'] * comments_max_nr
csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
csvout = csv.writer(open(csvfile, 'w', newline=''))

# Write CSV Header
csvout.writerow((
    'Key',  # Github issue number
    'Summary',  # Github title
    'Type',  # Need Zenhub API for this (Story, epic, bug)
    'Status',  # Need Zenhub API for this (in which pipeline is located)
    'Resolution',  # Need Zenhub API for this (done, won't do, duplicate, cannot reproduce) - for software projects
    'Fix Version(s)',  # milestone
    'Description',  # Description
    'Assignee',  # Assignee
    'Reporter',  # Created by
    'Created',  # Created at
    'Updated',  # Updated at
    'Resolved',  # Closed at
    'Estimate',  # Estimate
    'Epic Name',
    'Epic Link',
    'Issue Id',
    'Parent Id',
    *labels_header_list,  # Labels
    *comments_header_list,
      # Comments
))
write_epic(total_result)
write_issue(total_result)
