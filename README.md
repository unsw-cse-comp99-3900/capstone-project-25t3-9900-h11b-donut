# AI Learning Plan Management System

This repository contains a full-stack AI-driven intelligent learning plan management platform developed for the UNSW COMP9900 capstone project. It adopts a monorepo structure.

## Project Background

In university learning processes, students often face challenges such as numerous course tasks, time management difficulties, and lack of personalized learning guidance. To address these pain points, we have developed an AI-powered learning plan management system. This project is commissioned by Innovra client representative Jinglin Sun as an industry project for UNSW COMP9900 Capstone, aiming to build a web-based AI Learning Coach prototype system. The system centers on university course scenarios, automatically transforming syllabi, learning objectives, and various assessment nodes (assignments, quizzes, exams, etc.) into personalized, adaptively adjustable learning paths, helping students efficiently plan study time, track learning progress, and receive intelligent learning guidance throughout the semester.

The system achieves core functions such as intelligent learning plan generation, personalized learning suggestions, AI conversation tutoring, and intelligent question generation through integration with Google Gemini AI, providing students with comprehensive learning management and tutoring support. Additionally, the admin end offers course management, student monitoring, data analysis, and other functions, helping educators better understand student learning situations, identify at-risk students, and intervene promptly.

## Project Scope

### Intelligent Learning Plan Generation and Scheduling

The system analyzes students' course tasks, deadlines, and personal preferences (daily study time, weekly study days, dates to avoid learning, etc.) through Google Gemini API to automatically generate personalized weekly study plans. AI intelligently allocates daily study tasks and durations based on factors such as task difficulty, time urgency, and task weights, ensuring students can reasonably arrange time and efficiently complete coursework. Plan generation adopts a two-stage strategy: first using Gemini LLM to decompose tasks into multiple learning parts, then using intelligent scheduling algorithms to allocate these parts to optimal study time slots according to students' personal preferences.

### AI Learning Tutoring and Conversation System

Provides intelligent conversation functionality where students can ask AI about reasons for study plans, task details, learning methods, etc. Based on study plan context, AI provides personalized explanations, encouragement, and suggestions. The system maintains 7 days of conversation history, supporting contextually coherent multi-round conversations. Additionally, AI can automatically generate practice questions based on students' self-provided weak knowledge points and provide instant scoring and detailed feedback. The conversation system adopts a state machine architecture, supporting multiple conversation modes (welcome, explain plan, practice setup, practice in progress, etc.), ensuring smooth and natural conversations.

### AI Question Generation and Intelligent Scoring

The system integrates a complete AI question generation and automatic scoring module. Administrators can upload sample questions to the database, and AI generates new practice questions based on these examples (supporting Multiple Choice Questions MCQ and Short Answer). After students submit answers, the system automatically scores: MCQs are judged instantly, while short answers are semantically analyzed and multi-dimensionally scored by AI (correctness, completeness, clarity). Scoring results include personalized hints, complete solutions, and detailed feedback, helping students understand mistakes and improve.

### Learning Progress Tracking and Risk Identification

The system tracks students' learning progress and task completion status in real-time. Each task supports 0-100% progress updates, and students can view their learning completion status at any time. The admin end can monitor all students' learning situations, view progress trend charts, and identify at-risk students through algorithms (based on the number of overdue tasks and consecutive days of incomplete completion). The system automatically generates student risk reports and grades risk levels from high to low with colors from red to green, helping educators promptly identify students needing assistance and take intervention measures.

### System Architecture

The backend uses Django 5.2.7 + Django REST Framework to build a RESTful API architecture, using MySQL database (production environment) or SQLite (development environment) for data persistence. The frontend is built as a modern single-page application based on React 19 + TypeScript 5.9 + Vite 7, using Zustand for lightweight state management and Recharts for data visualization. The system supports Docker containerized deployment, implementing one-click startup of frontend and backend services through docker-compose orchestration. Nginx is used as a reverse proxy server to handle static file serving and API request forwarding.

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Custom Store mode
- **Routing**: Hash-based routing
- **Styling**: CSS-in-JS

### Backend
- **Framework**: Django
- **Database**: TiDB, Mysql,SQLite (development environment)
- **API**: RESTful API
- **Forward Proxy Server**
- **Reverse SSH Tunnel**

### Core Functions/User Interfaces

**Student Functions:**
- **Dashboard (Student Homepage)**: Displays course overview cards, DDL approaching reminder lists, learning progress statistics, quick navigation entries, unread message notifications
- **Course Management**: Browse optional course lists, search courses, join/exit courses, view course detail pages, access course learning materials, view task lists and deadlines, download PDF materials
- **Study Plan**: View AI-generated weekly study plans (weekly view calendar), daily task card display, task completion status toggle, progress bar display, multi-week plan switching, regenerate plans, adjust study arrangements
- **AI Chat Coach**: Conduct multi-round conversations with AI, get learning suggestions and encouragement, explain reasons for study plans, generate personalized practice questions (MCQ/Short Answer), instant AI scoring feedback, view conversation history (7 days)
- **Profile Management**: Manage personal information, set learning preferences (daily study duration, weekly study days, avoid study dates), upload avatars, save as default preferences
- **Message Center**: View DDL reminders, reward messages, system notifications, mark as read/unread, batch operations

**Administrator Functions:**
- **Admin Dashboard**: Data statistics cards (total courses, total students, total tasks), course management overview, recent activity display, quick operation entries
- **Course Management**: Create courses (course code, name, description, illustration selection), edit course information, delete courses, course existence checking
- **Task Management**: Create tasks (title, deadline, description, weight percentage, reference links), edit tasks, delete tasks (optionally delete associated files), upload task files
- **Material Management**: Upload learning materials (PDFs, documents, etc.), create material entries, edit material information, delete materials, file management
- **Question Bank**: Upload sample questions (JSON/TXT format), batch question import, view question lists, edit questions, delete questions, support MCQ and Short Answer types
- **Progress Trend**: View course student lists, view student task progress, progress trend chart display, filter specific tasks, overdue task statistics
- **Risk Report**: Identify at-risk students based on algorithms, view student risk reports (overdue task count, consecutive incomplete days), generate risk summaries, export reports

---

## Project Structure

```
capstone-project-25t3-9900-h11b-donut/
├── front_end/              # React + TypeScript frontend application
│   ├── src/              # Source code directory
│   │   ├── pages/       # Page components (13 main pages)
│   │   │   ├── StudentHome/      # Student dashboard
│   │   │   ├── StudentPlan/      # Study plan view
│   │   │   ├── ChatWindow/      # AI chat interface
│   │   │   └── AdminHome/      # Admin dashboard
│   │   ├── components/  # Reusable UI components
│   │   │   ├── AIChatWidget.tsx     # AI chat widget
│   │   │   ├── AvatarPicker.tsx     # Avatar selection
│   │   │   └── Header.tsx          # Page header
│   │   ├── services/    # API integration layer
│   │   │   ├── api.ts              # Core API client
│   │   │   ├── aiChatService.ts    # Chat API wrapper
│   │   │   └── aiPlanService.ts    # Plan API wrapper
│   │   ├── store/       # State management (Zustand)
│   │   │   ├── coursesStore.ts     # Course state
│   │   │   └── preferencesStore.ts # User preferences
│   │   └── utils/       # Utility functions
│   ├── public/            # Static assets
│   │   ├── sample-*.json       # Question samples
│   │   └── images/            # UI illustrations
│   ├── package.json       # NPM dependencies
│   |── vite.config.ts    # Vite build config
|   |__ test
|         |__ test_frontend_complete.py # front_end test file
|
├── django_backend/         # Django REST API backend
│   ├── stu_accounts/     # Student authentication module
│   ├── adm_accounts/     # Admin authentication module
│   ├── courses/          # Course management (CRUD operations)
│   ├── courses_admin/     # Admin course management
│   ├── plans/            # Study plan storage & retrieval
│   ├── preferences/        # User preference management
│   ├── task_progress/     # Progress tracking system
│   ├── ai_module/        # AI plan generation core
│   │   ├── plan_generator.py  # Main AI logic
│   │   ├── scheduler.py      # Time allocation
│   │   └── llm_structures.py # Gemini API integration
│   ├── ai_chat/          # AI conversation system
│   │   ├── chat_service.py   # Chat logic
│   │   └── models.py        # Message storage
│   ├── ai_question_generator/ # Practice question system
│   │   ├── generator.py      # Question generation
│   │   └── grader.py         # AI grading
│   │── reminder/         # Notification system
│   │    ├── models.py        # Message model
│   │    └── cron.py          # Scheduled reminders
│   │—— test/
│        │___ backend_test.md  # description of backend testing
│        │___ test_ai_unified.py # ai part test
│        │___ test_auth.py # basic function test1
│        │___ test_course_task.py # basic function test2
│        │___ test_plan_api_with_mocks.py # test ai plan with mock data
│
│
├── assets/               # Project-wide assets
│   └── CodeBubbyAssets/ # Development resources
|
├── docker-compose.yml     # Docker orchestration
├── docker-compose.server.yml # Production config
├── API_DOCUMENTATION.md   # Complete API reference
├── DEPLOYMENT_GUIDE.md  # Production deployment
├── TROUBLESHOOTING_GUIDE.md # Common issues
├── README.md            # This file
└── README_new.md        # Chinese version
```

## 🌟 Project Highlights
- **AI Two-Stage Plan Generation**: LLM task decomposition + intelligent scheduling algorithm, ensuring scientifically reasonable learning plans
- **Adaptive Learning Paths**: Dynamically adjust learning content and difficulty based on learning progress and weak points
- **Multimodal AI Tutoring**: Text conversation + question generation + automatic scoring, comprehensive learning support
- **Real-time Risk Early Warning**: Algorithm-based at-risk student identification, timely intervention to ensure learning effectiveness
- **7-Day Contextual Conversation**: Coherent multi-round AI conversation experience, providing continuous learning guidance
- **4-Level Preference Relief Strategy**: Progressive time arrangement adjustment, ensuring plan feasibility

## 🧮 Core Algorithms
### Intelligent Scheduling Algorithm
A multi-factor scoring system based on task weights, urgency, and student preferences. The algorithm considers factors such as task difficulty, deadline urgency, and personal learning habits to automatically calculate optimal time allocation. Time block allocation optimization avoids learning fatigue, automatically identifies optimal study time slots, ensuring maximum learning efficiency.

### Preference Relief Strategy
Adopts a 4-level tiered relief mechanism: original preference settings → expand study days → allow avoid dates → increase daily limit. Each tier is carefully designed to ensure plan executability while maintaining user's learning habits and preferences as much as possible.

### Risk Identification Algorithm
At-risk student identification adopts multi-dimensional evaluation: overdue task count weight 40%, consecutive incomplete days weight 60%. The system dynamically adjusts risk thresholds to adapt to characteristics of different semester stages, ensuring identification result accuracy and timeliness.

## 📊 Project Outcomes
### Technical Metrics
- API Response Time: 95% of requests completed within 200ms
- Frontend First Screen Loading: Average loading time less than 3 seconds
- Database Query Optimization: Average query time within an acceptable time range
- AI Generation Success Rate: Over 95% success rate

### Functional Completeness
- ✅ 13 core page modules, covering full process of student and admin ends
- ✅ 25+ REST API interfaces, supporting all business functions
- ✅ 8 types of AI function integration, including plan generation, conversation tutoring, question generation, automatic scoring
- ✅ Complete user permission system, supporting different roles for students and administrators

### Test Coverage
- Frontend Testing: 100% pass rate, containing 13 component and functionality tests
- Backend Testing: As Full as much coverage of API interfaces, AI integration, database operations. And explaination for more methods/cases to test/be tested
- End-to-End Testing: Complete business process verification

## 🏗️ System Architecture
The system adopts a front-end and back-end separated architecture, exchanging data through RESTful APIs. The front-end React application accesses the back-end Django service through Nginx reverse proxy. AI modules provide intelligent functions through Google Gemini API, and the database uses MySQL/SQLite for data persistence. Docker containerized deployment supports one-click startup, ensuring consistency between development and production environments.

---

## Functional Modules

### Student Functions
1. **User Authentication**
   - Student registration/login
   - login time record
   - Token persistence

2. **Personal Profile Management**
   - Avatar upload and display
   - Personal information editing
   - Preference settings

3. **Course Management**
   - View optional courses
   - Join/exit courses
   - Course detail viewing

4. **Study Plan**
   - AI-generated study plans
   - Weekly plan view
   - Progress tracking

5. **AI Conversation Function**
   - Intelligent study plan explanation
   - Task detail explanation
   - Learning encouragement and support
   - 7-day conversation history storage
   - Practice question explanation and answering

### Administrator Functions
1. **Administrator Authentication**
   - Administrator registration/login
   - Independent route protection

2. **Dashboard**
   - Data statistics display
   - Course management overview
   - Student status monitoring

3. **Course Management**
   - Create/edit courses
   - Student progress viewing
   - Task management

### System Functions
1. **Real Time notification**
   - Monitor tasks deadline for every students
   - Monitor each student's status of completeing one day's work

2. **log In status check**
   - maintain valid status for 30 minutes and token automatically expires
   - Remote login detection: each account can only be logged in by one user at a time.
   - Route protection mechanism

## Setup & Run

# Quick Start(After cloning the repository)

## Backend (Local)

```bash
cd django_backend
python -m venv .venv
.venv\\scripts\\activate       # (Windows)
# or
source .venv/bin/activate    # (Mac)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

🔗 http://127.0.0.1:8000/

---

## Frontend (Local)

```bash
cd front_end
npm install
npm run dev
```

🔗 http://localhost:5173

---

## Docker (Backend + Frontend)

Run following command from project root directory to build and start all services:

```bash
docker-compose up --build #with docker desktop running
```

Backend  → http://0.0.0.0:8000/ 
Frontend → http://localhost:5173/

> **Note**  
> This project provides three different methods to start the application.  
> The method described above is the most convenient and allows users to experience approximately **90% of all features**.  
> The other two methods require a remote server and involve more advanced setup steps.  
> For detailed instructions on all three startup methods, please refer to the **Installation Manual**.

# Testing

Our testing follows the overall testing standards of the project, focusing on ensuring API consistency, correctness of study-plan generation logic, and stability of persisted data.
Focused on backend, due to various functionalities, we decide to test some basic and also core functionalities. 
---
## Backend

## Unit Tests

Unit tests primarily cover:

### User Authentication
- Login, registration, and identity validation  
- Error paths for invalid credentials and insufficient permissions  

### Course & Task Management
- Course creation / deletion / listing /enrolment
- Task creation, weight/percentage validation, and deadline handling  
- Cascading cleanup logic for `TaskProgress` when deleting courses or tasks  

### Generate AI plan with mock data
- Correct generation when system cannot call external api gemini or task file is missing

---

## Integration Tests

Integration tests verify end-to-end flow across multiple components:

### End-to-End API Flow
From course creation → plan generation → marking tasks complete → overdue updates.  
Ensures cross-module behavior remains stable and predictable.

### AI Modules (Core Unit Tests)
- AI Study Plan Generation
- AI Chat
- AI-Generated Practice Questions 

### Database Persistence
- Multi-model interactions: `Course` → `CourseTask` → `TaskProgress`  
- Database state remains consistent after deletion of courses or tasks  

 
To see full backend testing strategy:
[django_backend/test/backend_test.md](django_backend/test/backend_test.md)

## Frontend

Our frontend behavior is validated using a standalone Python test harness (`test_frontend_complete.py`) that simulates key UI workflows, routing rules, and page-level state transitions. Tests are organised into logical categories so we can verify each major feature of the web app in isolation.

### Authentication & Navigation
- **Authentication validation**  
  - Email & password checks for login (format, minimum length).  
  - zID and name validation for signup (e.g., `z1234567` pattern, non-empty name).
- **Role-aware routing**  
  - Guest, student, and admin access to `/student-home`, `/student-plan`, `/admin-home`, `/practice-session`.  
  - Public routes remain accessible to unauthenticated users, while protected routes are restricted by role.

### Student & Admin Pages
- **Student Home**  
  - Priority deadline filtering (e.g., "high" priority tasks).  
  - Overall progress aggregation across enrolled courses.
- **Study Plan**  
  - Toggling task completion state.  
  - Recomputing completion percentages and ensuring the task list remains consistent.
- **Practice Session**  
  - Session configuration (course, topic, question count, difficulty).  
  - Question generation, answer submission, and score calculation.
- **Admin Courses**  
  - Course lookup by ID.  
  - Enrollment vs active student rates.  
  - Identification of "at-risk" courses based on completion-rate thresholds.

### Components, AI & Responsive Behaviour
- **Components**  
  - Avatar picker: category filters and avatar selection.  
  - Chat messages: sender ownership, read/unread state, and unread count.  
  - Help modal: open/close behavior, tab switching, search, and section filtering.
- **AI chat integration**  
  - Mocked AI chat service with modes: `general`, `explain_plan`, `practice`.  
  - Mode switching, context-appropriate responses, suggestion lists, and conversation summaries.
- **Responsive design**  
  - Device-type detection (mobile / tablet / desktop) based on screen width.  
  - Layout configuration (sidebar presence, column count, compact chat mode).  
  - Feature visibility rules (e.g., touch gestures only on mobile, keyboard shortcuts on desktop).

### Error Handling
- Form-level validation for empty fields, invalid email formats, numeric ranges, and missing required fields.  
- File-upload checks (missing file, size limit, MIME type).  
- Simulated network, database, and permission errors to ensure they are detected and handled gracefully.

Each test logs its category, status, and execution time, and the suite produces a JSON summary (`frontend_complete_results.json`) with the overall success rate. This provides deterministic verification that frontend logic behaves consistently across roles, devices, and edge cases, independent of the live backend and browser environment.

To see full frontend testing strategy:  
[`front_end/test/test_frontend_complete.py`](front_end/test/test_frontend_complete.py)
Test method(already in virtual environment):
```bash
cd front_end
cd test
python test_frontend_complete.py
# test results can be checked in the file:/front_end/test/frontend_complete_results.json
```