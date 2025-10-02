# Counselor Dashboard Revamp TODO

## Step 1: Update models.py
- [x] Add helper functions: get_student_results(student_id), get_all_students(), get_programs(), get_results_aggregates()
- [x] Ensure functions check DB and return empty lists if no data

## Step 2: Update app.py
- [x] Add role checks for counselor access to /counselor/... routes
- [x] Add new route: /counselor/results/<student_id> to fetch and display student results
- [x] Add new route: /counselor/generate_graph to return JSON data for Chart.js
- [x] Enhance existing routes for program/assessment CRUD with better error handling

## Step 3: Update templates/counselor_dashboard.html
- [ ] Revamp UI: Clean layout with sections for Users, Results, Programs, Research
- [ ] Users section: Show total students, list with basic info, click to view results
- [ ] Results section: Table for selected student's results
- [ ] Programs section: List programs/assessments, add/remove buttons, empty state messages
- [ ] Research section: Integrate Chart.js for graphs, buttons to generate visualizations
- [ ] Ensure no student-only features, database-driven data only

## Step 4: Testing and Verification
- [ ] Test all buttons and forms for CRUD operations
- [ ] Verify empty states when no data exists
- [ ] Check graphs load correctly with real data
- [ ] Ensure only counselor can access the page
