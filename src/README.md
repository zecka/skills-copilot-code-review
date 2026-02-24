# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Display active announcements from the database
- Manage announcements (create, edit, delete) for signed-in teachers

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/auth/login?username={username}&password={password}`             | Sign in as teacher/admin                                            |
| GET    | `/auth/check-session?username={username}`                         | Validate signed-in user                                             |
| GET    | `/announcements/active`                                           | Get active announcements for public banner                          |
| GET    | `/announcements?teacher_username={username}`                      | Get all announcements (requires sign-in)                            |
| POST   | `/announcements?teacher_username={username}`                      | Create announcement (requires sign-in)                              |
| PUT    | `/announcements/{announcement_id}?teacher_username={username}`    | Update announcement (requires sign-in)                              |
| DELETE | `/announcements/{announcement_id}?teacher_username={username}`    | Delete announcement (requires sign-in)                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in MongoDB and initialized from `backend/database.py` when collections are empty.
