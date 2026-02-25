import urllib.request, json, urllib.parse, io

BASE = 'http://localhost:8000/api/v1'

def api_call(path, method='GET', data=None, token=None, files=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    body = None
    if files:
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        body = b''
        for field, (filename, content) in files.items():
            body += f'--{boundary}\r\n'.encode()
            body += f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
            body += b'Content-Type: text/csv\r\n\r\n'
            body += content.encode() + b'\r\n'
        body += f'--{boundary}--\r\n'.encode()
    elif data:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(data).encode()

    req = urllib.request.Request(f'{BASE}{path}', data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print("--- DIAGNOSTIC START ---")

# 1. Login as admin
s, login_data = api_call('/auth/login', 'POST', {'email':'admin@college.edu', 'password':'Admin@1234'})
if s != 200:
    print(f'ADMIN LOGIN FAILED: {s} {login_data}')
    exit(1)
token = login_data['access_token']
print(f'ADMIN LOGIN: SUCCESS (Token starts with {token[:10]}...)')

# 2. Try upload as admin
csv_content = 'student_id,age,gender,department,semester,attendance_pct,assignment_score_avg,internal_marks_avg,semester_gpa,study_hours_per_week,participation_score,prev_semester_gpa,backlogs,financial_aid\nS999,20,Male,CSE,3,80.0,75.0,70.0,7.5,15.0,6.0,7.0,0,False'
print("Attempting upload as admin...")
s, upload_data = api_call('/upload/csv', 'POST', token=token, files={'file': ('test.csv', csv_content)})
print(f'UPLOAD AS ADMIN STATUS: {s}')
print(f'UPLOAD AS ADMIN RESPONSE: {upload_data}')

# 3. Login as viewer
print("\nAttempting upload as viewer...")
s, login_data_v = api_call('/auth/login', 'POST', {'email':'viewer@college.edu', 'password':'Viewer@1234'})
token_v = login_data_v['access_token']
s, upload_data_v = api_call('/upload/csv', 'POST', token=token_v, files={'file': ('test.csv', csv_content)})
print(f'UPLOAD AS VIEWER STATUS: {s}')
print(f'UPLOAD AS VIEWER RESPONSE (expected 403): {upload_data_v}')
